# -*- coding: utf-8 -*-
#
# This file is part of FNP-Redakcja, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from slughifi import slughifi
from catalogue.helpers import cached_in_field
from catalogue.models import BookPublishRecord, ChunkPublishRecord
from catalogue.signals import post_publish
from catalogue.tasks import refresh_instance
from catalogue.xml_tools import compile_text, split_xml


class Book(models.Model):
    """ A document edited on the wiki """

    title = models.CharField(_('title'), max_length=255, db_index=True)
    slug = models.SlugField(_('slug'), max_length=128, unique=True, db_index=True)
    gallery = models.CharField(_('scan gallery name'), max_length=255, blank=True)

    #wl_slug = models.CharField(_('title'), max_length=255, null=True, db_index=True, editable=False)
    parent = models.ForeignKey('self', null=True, blank=True, verbose_name=_('parent'), related_name="children")
    parent_number = models.IntegerField(_('parent number'), null=True, blank=True, db_index=True)

    # Cache
    _short_html = models.TextField(null=True, blank=True, editable=False)
    _single = models.NullBooleanField(editable=False, db_index=True)
    _new_publishable = models.NullBooleanField(editable=False)
    _published = models.NullBooleanField(editable=False)

    # Managers
    objects = models.Manager()

    class NoTextError(BaseException):
        pass

    class Meta:
        app_label = 'catalogue'
        ordering = ['parent_number', 'title']
        verbose_name = _('book')
        verbose_name_plural = _('books')
        permissions = [('can_pubmark', 'Can mark for publishing')]


    # Representing
    # ============

    def __iter__(self):
        return iter(self.chunk_set.all())

    def __getitem__(self, chunk):
        return self.chunk_set.all()[chunk]

    def __len__(self):
        return self.chunk_set.count()

    def __nonzero__(self):
        """
            Necessary so that __len__ isn't used for bool evaluation.
        """
        return True

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ("catalogue_book", [self.slug])


    # Creating & manipulating
    # =======================

    @classmethod
    def create(cls, creator, text, *args, **kwargs):
        b = cls.objects.create(*args, **kwargs)
        b.chunk_set.all().update(creator=creator)
        b[0].commit(text, author=creator)
        return b

    def add(self, *args, **kwargs):
        """Add a new chunk at the end."""
        return self.chunk_set.reverse()[0].split(*args, **kwargs)

    @classmethod
    def import_xml_text(cls, text=u'', previous_book=None,
                commit_args=None, **kwargs):
        """Imports a book from XML, splitting it into chunks as necessary."""
        texts = split_xml(text)
        if previous_book:
            instance = previous_book
        else:
            instance = cls(**kwargs)
            instance.save()

        # if there are more parts, set the rest to empty strings
        book_len = len(instance)
        for i in range(book_len - len(texts)):
            texts.append(u'pusta część %d' % (i + 1), u'')

        i = 0
        for i, (title, text) in enumerate(texts):
            if not title:
                title = u'część %d' % (i + 1)

            slug = slughifi(title)

            if i < book_len:
                chunk = instance[i]
                chunk.slug = slug
                chunk.title = title
                chunk.save()
            else:
                chunk = instance.add(slug, title, adjust_slug=True)

            chunk.commit(text, **commit_args)

        return instance

    def make_chunk_slug(self, proposed):
        """ 
            Finds a chunk slug not yet used in the book.
        """
        slugs = set(c.slug for c in self)
        i = 1
        new_slug = proposed
        while new_slug in slugs:
            new_slug = "%s_%d" % (proposed, i)
            i += 1
        return new_slug

    def append(self, other, slugs=None, titles=None):
        """Add all chunks of another book to self."""
        number = self[len(self) - 1].number + 1
        len_other = len(other)
        single = len_other == 1

        if slugs is not None:
            assert len(slugs) == len_other
        if titles is not None:
            assert len(titles) == len_other
            if slugs is None:
                slugs = [slughifi(t) for t in titles]

        for i, chunk in enumerate(other):
            # move chunk to new book
            chunk.book = self
            chunk.number = number

            if titles is None:
                # try some title guessing
                if other.title.startswith(self.title):
                    other_title_part = other.title[len(self.title):].lstrip(' /')
                else:
                    other_title_part = other.title

                if single:
                    # special treatment for appending one-parters:
                    # just use the guessed title and original book slug
                    chunk.title = other_title_part
                    if other.slug.startswith(self.slug):
                        chunk_slug = other.slug[len(self.slug):].lstrip('-_')
                    else:
                        chunk_slug = other.slug
                    chunk.slug = self.make_chunk_slug(chunk_slug)
                else:
                    chunk.title = "%s, %s" % (other_title_part, chunk.title)
            else:
                chunk.slug = slugs[i]
                chunk.title = titles[i]

            chunk.slug = self.make_chunk_slug(chunk.slug)
            chunk.save()
            number += 1
        other.delete()


    # State & cache
    # =============

    def last_published(self):
        try:
            return self.publish_log.all()[0].timestamp
        except IndexError:
            return None

    def publishable(self):
        if not self.chunk_set.exists():
            return False
        for chunk in self:
            if not chunk.publishable():
                return False
        return True

    def hidden(self):
        return self.slug.startswith('.')

    def is_new_publishable(self):
        """Checks if book is ready for publishing.

        Returns True if there is a publishable version newer than the one
        already published.

        """
        new_publishable = False
        if not self.chunk_set.exists():
            return False
        for chunk in self:
            change = chunk.publishable()
            if not change:
                return False
            if not new_publishable and not change.publish_log.exists():
                new_publishable = True
        return new_publishable
    new_publishable = cached_in_field('_new_publishable')(is_new_publishable)

    def is_published(self):
        return self.publish_log.exists()
    published = cached_in_field('_published')(is_published)

    def is_single(self):
        return len(self) == 1
    single = cached_in_field('_single')(is_single)

    @cached_in_field('_short_html')
    def short_html(self):
        return render_to_string('catalogue/book_list/book.html', {'book': self})

    def touch(self):
        update = {
            "_new_publishable": self.is_new_publishable(),
            "_published": self.is_published(),
            "_single": self.is_single(),
            "_short_html": None,
        }
        Book.objects.filter(pk=self.pk).update(**update)
        refresh_instance(self)

    def refresh(self):
        """This should be done offline."""
        self.short_html
        self.single
        self.new_publishable
        self.published

    # Materializing & publishing
    # ==========================

    def get_current_changes(self, publishable=True):
        """
            Returns a list containing one Change for every Chunk in the Book.
            Takes the most recent revision (publishable, if set).
            Throws an error, if a proper revision is unavailable for a Chunk.
        """
        if publishable:
            changes = [chunk.publishable() for chunk in self]
        else:
            changes = [chunk.head for chunk in self if chunk.head is not None]
        if None in changes:
            raise self.NoTextError('Some chunks have no available text.')
        return changes

    def materialize(self, publishable=False, changes=None):
        """ 
            Get full text of the document compiled from chunks.
            Takes the current versions of all texts
            or versions most recently tagged for publishing,
            or a specified iterable changes.
        """
        if changes is None:
            changes = self.get_current_changes(publishable)
        return compile_text(change.materialize() for change in changes)

    def publish(self, user):
        """
            Publishes a book on behalf of a (local) user.
        """
        raise NotImplementedError("Publishing not possible yet.")

        from apiclient import api_call

        changes = self.get_current_changes(publishable=True)
        book_xml = self.materialize(changes=changes)
        #api_call(user, "books", {"book_xml": book_xml})
        # record the publish
        br = BookPublishRecord.objects.create(book=self, user=user)
        for c in changes:
            ChunkPublishRecord.objects.create(book_record=br, change=c)
        post_publish.send(sender=br)