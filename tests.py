import time, datetime, pytz, pdb

from django.test import TestCase, TransactionTestCase
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.core.cache import cache

from general.models import AuthKey
from blog.models import Post, Tag
from general.functions import parse_post_content, rand_str_gen

def authenticate(self):
	self.client.get(reverse('general:login'))
	a = AuthKey.objects.all()[0]
	self.client.post(reverse('general:login'),{'text': a.text})

def unauthenticate(self):
	self.client.get(reverse('general:logout'))
	
class BlogViewTests(TestCase):
	def test_index_view_with_non_draft_post(self):
		"""
		If a non_draft_post exists, it should be returned 
		"""
		now = timezone.now()
		Post.objects.create(title="TEST1", pub_date=now)
		response_post = self.client.get(reverse('blog:index')).context['posts'][0]

		self.assertEqual(response_post['title'], "TEST1")
		self.assertEqual(response_post['content'], "Fill me with content")
		self.assertEqual(response_post['pub_date'], now.replace(microsecond=0))
		self.assertEqual(response_post['tag_names'], [])
		self.assertEqual(response_post['draft'], False)
		
	def test_index_view_with_draft_post(self):
		"""
		If draft post exists, it should not be returned
		"""
		Post.objects.create(draft = True)
		response = self.client.get(reverse('blog:index'))
		self.assertQuerysetEqual(response.context['posts'], [])

	def test_index_view_with_draft_and_non_draft_posts(self):
		"""
		If draft and non-draft posts exist, only the non-draft post 
		should be returned
		"""
		now = timezone.now()
		Post.objects.create(title="TEST3", pub_date=now)
		Post.objects.create(title="TEST4", draft=True)
		response_post = self.client.get(reverse('blog:index')).context['posts'][0]
		
		self.assertEqual(response_post['title'], "TEST3")
		self.assertEqual(response_post['content'], "Fill me with content")
		self.assertEqual(response_post['pub_date'], now.replace(microsecond=0))
		self.assertEqual(response_post['tag_names'], [])
		self.assertEqual(response_post['draft'], False)
	
	def test_index_view_with_multiple_non_draft_posts(self):
		"""
		If multiple non-draft posts exist, they should all be returned
		"""
		time1 = timezone.now()
		Post.objects.create(title="TEST5", pub_date = time1)
		time.sleep(1)
		time2 = timezone.now()
		Post.objects.create(title="TEST6", pub_date = time2)
		Post.objects.create(title="TEST7")
		response_posts = self.client.get(reverse('blog:index')).context['posts']

		self.assertEqual(response_posts[0]['title'], "TEST6")
		self.assertEqual(response_posts[0]['content'], "Fill me with content")
		self.assertEqual(response_posts[0]['pub_date'], time2.replace(microsecond=0))
		self.assertEqual(response_posts[0]['tag_names'], [])
		self.assertEqual(response_posts[0]['draft'], False)

		self.assertEqual(response_posts[1]['title'], "TEST5")
		self.assertEqual(response_posts[1]['content'], "Fill me with content")
		self.assertEqual(response_posts[1]['pub_date'], time1.replace(microsecond=0))
		self.assertEqual(response_posts[1]['tag_names'], [])
		self.assertEqual(response_posts[1]['draft'],  False)
	
	def test_add_view_unauthenticated(self):
		"""
		POST methods sent to blog:add should return a 404 error if they are
		not authenticated
		"""
		response=self.client.get(reverse('blog:add'))
		self.assertEqual(response.status_code, 404)

	def test_add_view(self):
		"""
		POST Methods sent to blog:add should create a new post object with
		the appropriate content, tags, and title if authenticated
		"""
		authenticate(self)
		response=self.client.get(reverse('blog:add'))
		self.assertEqual(response.status_code, 200)

		self.client.post(reverse('blog:add'),
								  {'title': 'TEST1',
								   'content':'TEST1',
								   'tags': 'b, c, a',
								   'draft': False})
		p = Post.objects.all()[0]
		self.assertEqual(p.title, 'TEST1')
		self.assertEqual(p.content, 'TEST1')
		self.assertEqual(p.tags.all()[0].title, 'a')
		self.assertEqual(p.tags.all()[1].title, 'b')
		self.assertEqual(p.tags.all()[2].title, 'c')

		self.client.post(reverse('blog:add'),
								  {'title': 'TEST2',
								   'content': 'TEST2',
								   'tags': 'tesing, tes2',
								   'draft': False})
		tag_list = Tag.objects.all()
		self.assertEqual(tag_list[0].title, 'a')
		self.assertEqual(tag_list[1].title, 'b')
		self.assertEqual(tag_list[2].title, 'c')
		self.assertEqual(tag_list[3].title, 'tes2')
		unauthenticate(self)

	def test_edit_view_unauthenticated(self):
		"""
		POST methods sent to blog:edit should return a 404 error if they are
		not authenticated
		"""
		response=self.client.get(reverse('blog:edit', args=(1,)))
		self.assertEqual(response.status_code, 404)

	def test_edit_view(self):
		"""
		POST Methods sent to blog:edit should modify an existing post object with
		new content, tags, and title
		"""
		old_p = Post.objects.create(title = "TEST1", 
		 				  draft = True, 
						  content = "Testing content")
		old_p.set_tags_for_post(['test','test1'])
		self.client.post(reverse('blog:edit', args=(old_p.pk,)),
								 {'title': 'TEST2',
								  'content': 'Tested cibtes',
								  'tags': 'test, test2'
								 })

		new_p = Post.objects.get(pk = old_p.pk)
		self.assertEqual(new_p.title, 'TEST2')
		self.assertEqual(new_p.content, 'Tested cibtes')
		self.assertEqual(new_p.draft, False)

		tag_list = Tag.objects.all()
		self.assertEqual(tag_list[0].title, 'test')
		self.assertEqual(tag_list[1].title, 'test2')
	
	def test_delete_view_unauthenticated(self):
		"""
		POST methods sent to blog:remove should return a 404 error if they 
		are not authenticated
		"""
		p1 = Post.objects.create(title="TEST1")
		p1.set_tags_for_post(['test','test1'])
		p2 = Post.objects.create(title="TEST2")
		p2.set_tags_for_post(['test','test2'])

		response=self.client.post(reverse('blog:delete'), {'pk': p2.pk})
	
		post_set = Post.objects.all()
		self.assertEqual(len(post_set), 2)
		self.assertEqual(post_set[0], p1)

		tag_set = Tag.objects.all()
		self.assertEqual(tag_set[0].title, 'test')
		self.assertEqual(tag_set[1].title, 'test1')
		self.assertEqual(tag_set[2].title, 'test2')

	def test_delete_view(self):
		"""
		POST Method sent to blog:delete should delete the post with the pk given
		by the POST method, check all its tags to see if they have other 
		associated posts, and delete them if they don't
		"""
		authenticate(self)
		p1 = Post.objects.create(title="TEST1")
		p1.set_tags_for_post(['test','test1'])
		p2 = Post.objects.create(title="TEST2")
		p2.set_tags_for_post(['test','test2'])

		self.client.post(reverse('blog:delete'), {'pk': p2.pk})

		post_set = Post.objects.all()
		self.assertEqual(len(post_set), 1)
		self.assertEqual(post_set[0], p1)
		self.assertEqual(Tag.objects.all()[0].title, 'test')
		self.assertEqual(Tag.objects.all()[1].title, 'test1')
		unauthenticate(self)

	def test_view_single_post(self):
		"""
		This url should return a single post to display
		"""
		now = timezone.now()
		p=Post.objects.create(title="TESTVIEW", pub_date=now)
		p.set_tags_for_post(['test', 'test1'])
		response=self.client.get(reverse('blog:view_single_post', args=(p.pk,)))

		post = response.context['posts'][0]
		
		self.assertEqual(post['title'], 'TESTVIEW') 
		self.assertEqual(post['draft'], False) 
		self.assertEqual(post['tag_names'], ['test', 'test1']) 
		self.assertEqual(post['content'], 'Fill me with content') 
		self.assertEqual(post['pub_date'], now.replace(microsecond=0)) 

class PostMethodTests(TestCase):
	def test_build_post_dict(self):
		"""
		build_post_dict should return a dictionary of populated post objects		"""
		post1 = Post(
			title="TEST1", 
			draft=True, 
			pub_date=datetime.datetime(2013, 4, 16, 19, 1, 2).replace(tzinfo=pytz.UTC),
			content="TEST11\r\n11<br/>11")
		post1.save()
		tag1 = Tag(title="TAG111")
		tag1.save()
		post1.tags.add(tag1)
		self.assertEqual(
			post1.build_post_dict('display'),
			{
				'title': 'TEST1', 
				'content': 'TEST11<br/>11<br/>11', 
				'tag_names': [u'TAG111'], 
				'draft': True, 
				'pk': 1L,
				'pub_date': datetime.datetime(2013, 4, 16, 19, 1, 2).replace(tzinfo=pytz.UTC)
			}
		)
		self.assertEqual(
			post1.build_post_dict('edit'),
			{
				'title': 'TEST1', 
				'content': 'TEST11\r\n11\r\n11', 
				'tag_names': [u'TAG111'], 
				'draft': True, 
				'pk': 1L,
				'pub_date': datetime.datetime(2013, 4, 16, 19, 1, 2).replace(tzinfo=pytz.UTC)
			}
		)
		
