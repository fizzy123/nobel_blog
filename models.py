from django.db import models
from django.utils import timezone

from general.functions import parse_post_content

import pdb

class Tag(models.Model):
	title = models.CharField(max_length=200, primary_key=True)
	
	def __unicode__(self):
		return self.title

class Post(models.Model):
	title = models.CharField(max_length=200, default='Give me a Title')
	content = models.TextField(default='Fill me with content')
	draft = models.BooleanField(default=False)
	pub_date = models.DateTimeField(null=True, blank=True)
	tags = models.ManyToManyField(Tag, blank = True)

	def __unicode__(self):
		return self.title
	
	def build_post_dict(self, mode):
		post_dict = {}
		post_dict['title'] = self.title
		post_dict['pk'] = self.pk
		post_dict['content'] = parse_post_content(self.content, mode)
		post_dict['draft'] = self.draft
		if self.pub_date:
		    post_dict['pub_date'] = self.pub_date
		post_dict['tag_names'] = []
		if self.tags:
			for tag in self.tags.all():
				post_dict['tag_names'].append(tag.title)
		return post_dict

	def set_tags_for_post(self, tags):
		old_tag_list = list(self.tags.all())
		self.tags.clear()
		for tag in tags:
			t = Tag.objects.get_or_create(title=tag)
			self.tags.add(t[0])
			t[0].save()
			self.save()
		self.save()
		for tag in old_tag_list:
			if not len(tag.post_set.all()):
				tag.delete()
		return self

