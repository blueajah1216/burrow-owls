"""Account and cross-media gallery checks against an isolated SQLite database."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.update(DATABASE_URL='sqlite:///:memory:', SECRET_KEY='local-gallery-check', MUSIC_AUTOREFRESH='0')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bs4 import BeautifulSoup
from app import app, db
import fineart
import photography
import fineart_auth as auth

HOST='https://thegreatgallery.art'
PASSWORD='a-test-password-123'

class GalleryChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING']=True
        cls.painting=next(p['id'] for p in fineart.load()['paintings'] if not p.get('n'))
        cls.photo=next(iter(photography.load()['by_id']))
        while photography.load()['by_id'][cls.photo].get('n'):
            cls.photo=next(p['id'] for p in photography.load()['by_id'].values() if not p.get('n'))
        cls.music='bach-1'
        cls.patcher=patch('app.get_site_visits',return_value=0);cls.patcher.start()
    @classmethod
    def tearDownClass(cls):cls.patcher.stop()
    def setUp(self):
        self.client=app.test_client()
        auth._attempts.clear()
        with app.app_context():
            auth.SavedItem.query.delete();auth.Favorite.query.delete();auth.Profile.query.delete();auth.User.query.delete();db.session.commit()
    def get(self,path,client=None):return (client or self.client).get(path,base_url=HOST)
    def post(self,path,data=None,json=None,client=None,csrf=True):
        client=client or self.client
        headers={}
        if csrf:
            # Session is keyed to the production host, just like the browser.
            token=BeautifulSoup(self.get('/account' if path.startswith('/account') else '/login',client).data,'html.parser').select_one('input[name=csrf]')
            if token:
                token=token['value']
            else:
                config=BeautifulSoup(self.get('/music',client).data,'html.parser').select_one('#gallery-config')
                import json as json_module
                token=json_module.loads(config.string)['csrf']
            if json is not None:headers['X-CSRF-Token']=token
            else:data=dict(data or {},csrf=token)
        return client.post(path,base_url=HOST,data=data,json=json,headers=headers)
    def signup(self,name='collector',client=None):
        response=self.post('/signup',dict(username=name,display_name='A Collector',password=PASSWORD,password2=PASSWORD),client=client)
        self.assertEqual(response.status_code,302,response.data)
        self.assertEqual(response.location,'/my-gallery')
    def add(self,**items):
        response=self.post('/api/gallery',json={'add':items})
        self.assertEqual(response.status_code,200,response.data)
        return response.json
    def test_legacy_paintings_and_new_types_share_one_gallery(self):
        self.signup()
        legacy=self.post('/api/favorites',json={'add':[self.painting]})
        self.assertEqual(legacy.json['ids'],[self.painting])
        data=self.add(photo=[self.photo],music=[self.music,'practice:hava-nagila'])
        self.assertEqual(data['counts'],dict(painting=1,photo=1,music=2))
        self.assertEqual(self.get('/api/favorites').json['ids'],[self.painting])
        page=self.get('/my-gallery');self.assertEqual(page.status_code,200)
        soup=BeautifulSoup(page.data,'html.parser')
        self.assertEqual(len(soup.select('.gg-item')),4)
        for link in soup.select('.gg-item a[href]'):
            self.assertFalse(link['href'].startswith('/fineart'))
            self.assertEqual(self.get(link['href']).status_code,200,link['href'])
        self.assertIn('private, no-store',page.headers['Cache-Control'])
        self.assertIn('noindex',page.headers['X-Robots-Tag'])
    def test_saves_are_idempotent_and_removals_persist(self):
        self.signup();self.add(painting=[self.painting,self.painting],photo=[self.photo],music=[self.music])
        self.add(painting=[self.painting],photo=[self.photo])
        data=self.post('/api/gallery',json={'remove':{'photo':[self.photo],'painting':[self.painting]}}).json
        self.assertEqual(data['counts'],dict(painting=0,photo=0,music=1))
        self.assertEqual(self.get('/api/gallery').json,data)
    def test_accounts_are_isolated(self):
        self.signup();self.add(photo=[self.photo],painting=[self.painting])
        second=app.test_client();self.signup('another',second)
        self.assertEqual(self.get('/api/gallery',second).json['counts'],dict(painting=0,photo=0,music=0))
        self.post('/api/gallery',json={'remove':{'painting':[self.painting]}},client=second)
        self.assertEqual(self.get('/api/gallery').json['counts']['painting'],1)
    def test_csrf_auth_and_validation(self):
        self.assertEqual(self.get('/api/gallery').status_code,401)
        self.assertTrue(self.get('/my-gallery').location.startswith('/login?next='))
        self.signup()
        self.assertEqual(self.post('/api/gallery',json={'add':{'photo':[self.photo]}},csrf=False).status_code,400)
        for payload in [[],{'add':[]},{'add':{'unknown':[]}},{'add':{'photo':'bad'}},{'remove':{'photo':[{}]} }]:
            self.assertEqual(self.post('/api/gallery',json=payload).status_code,400,payload)
        self.assertEqual(self.add(photo=['not-real'],music=['not-real'])['counts'],dict(painting=0,photo=0,music=0))
    def test_public_profiles_only_share_paintings(self):
        self.signup();self.add(painting=[self.painting],photo=[self.photo],music=[self.music])
        with app.app_context():uid=auth.User.query.first().id
        viewer=app.test_client()
        self.assertEqual(self.get(f'/lovers/{uid}',viewer).status_code,404)
        self.post('/account/public',dict(public='1'))
        public=self.get(f'/lovers/{uid}',viewer)
        self.assertEqual(public.status_code,200)
        self.assertNotIn(f'/photography/p/{self.photo}'.encode(),public.data)
        self.assertNotIn(f'/music/history/pieces/{self.music}'.encode(),public.data)
    def test_music_photo_and_painting_headers_recognize_login(self):
        self.signup()
        for path in ['/','/photography/','/music','/music/concerts','/music/history','/music/practice']:
            response=self.get(path);self.assertEqual(response.status_code,200,path)
            soup=BeautifulSoup(response.data,'html.parser')
            self.assertTrue(soup.select_one('.gg-account-links a[href="/my-gallery"]'),path)
            self.assertIn('no-store',response.headers['Cache-Control'])
    def test_safe_redirects(self):
        for bad in ['//evil.example','https://evil.example','/\\evil.example','/%2f%2fevil.example','/%252f%252fevil.example','/\tevil.example','/fineart//evil.example','/%66ineart/%2f/evil.example']:
            response=self.get('/login?next='+__import__('urllib.parse',fromlist=['quote']).quote(bad,safe=''))
            nxt=BeautifulSoup(response.data,'html.parser').select_one('input[name=next]')['value']
            self.assertEqual(nxt,'/my-gallery',bad)
        response=self.get('/login?next=/fineart/p/'+self.painting)
        self.assertEqual(BeautifulSoup(response.data,'html.parser').select_one('input[name=next]')['value'],'/p/'+self.painting)
    def test_form_fallback_and_filters(self):
        self.signup()
        response=self.post('/gallery/save',dict(kind='music',id=self.music,action='add',next='/music/history'))
        self.assertEqual(response.status_code,303);self.assertEqual(response.location,'/music/history')
        self.add(photo=[self.photo],painting=[self.painting])
        soup=BeautifulSoup(self.get('/my-gallery?kind=music&q=Bach').data,'html.parser')
        self.assertEqual(len(soup.select('.gg-item')),1)
        self.assertEqual(soup.select_one('.gg-item')['data-saved-kind'],'music')
        self.assertEqual(len(BeautifulSoup(self.get('/my-gallery?q=impossibleword').data,'html.parser').select('.gg-item')),0)
    def test_password_change_and_logout(self):
        self.signup();self.add(photo=[self.photo])
        fail=self.post('/account/password',dict(current_password='wrong',password='new-password-123',password2='new-password-123'))
        self.assertEqual(fail.status_code,400)
        ok=self.post('/account/password',dict(current_password=PASSWORD,password='new-password-123',password2='new-password-123'))
        self.assertEqual(ok.status_code,302)
        self.post('/logout')
        self.assertEqual(self.get('/api/gallery').status_code,401)
        login=self.post('/login',dict(username='collector',password='new-password-123'))
        self.assertEqual(login.status_code,302)
        self.assertEqual(self.get('/api/gallery').json['counts']['photo'],1)
    def test_delete_cascades_to_all_saved_data(self):
        self.signup();self.add(painting=[self.painting],photo=[self.photo],music=[self.music]);self.post('/account/public',dict(public='1'))
        self.assertEqual(self.post('/account/delete').status_code,302)
        with app.app_context():
            for model in [auth.User,auth.Favorite,auth.SavedItem,auth.Profile]:self.assertEqual(model.query.count(),0)
    def test_pagination_and_unavailable_items(self):
        self.signup()
        ids=list(photography.load()['by_id'])[:65]
        self.add(photo=[i for i in ids if not photography.load()['by_id'][i].get('n')])
        with app.app_context():
            uid=auth.User.query.first().id;db.session.add(auth.SavedItem(user_id=uid,kind='photo',item_id='retired-photo'));db.session.commit()
        soup=BeautifulSoup(self.get('/my-gallery').data,'html.parser')
        self.assertEqual(len(soup.select('.gg-item')),60)
        self.assertIn('Saved item no longer available',soup.get_text())
        self.assertGreater(len(BeautifulSoup(self.get('/my-gallery?page=2').data,'html.parser').select('.gg-item')),0)

if __name__=='__main__':unittest.main(verbosity=2)
