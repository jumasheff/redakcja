# -*- encoding: utf-8 -*-

__author__ = "Łukasz Rekucki"
__date__ = "$2009-09-25 09:35:06$"
__doc__ = "Module documentation."

import wlrepo

class MercurialDocument(wlrepo.Document):

    def data(self, entry):
        path = self._revision._docname + '.' + entry            
        return self._library._filectx(path, \
            self._revision.hgrev()).data()   

    def quickwrite(self, entry, data, msg, user=None):
        user = user or self.owner
        if user is None:
            raise ValueError("Can't determine user.")
        
        def write(l, r):
            f = l._fileopen(r(entry), "w+")
            f.write(data)
            f.close()
            l._fileadd(r(entry))

        return self.invoke_and_commit(write, lambda d: (msg, user))

    def invoke_and_commit(self, ops, before_commit):
        lock = self._library._lock()
        try:            
            self._library._checkout(self._revision.hgrev())

            def entry_path(entry):
                return self.id + '.' + entry
            
            ops(self._library, entry_path)
            message, user = before_commit(self)            
            self._library._commit(message, user)

            return self._library.document(docid=self.id, user=self.owner)
        finally:
            lock.release()            

    # def commit(self, message, user):
    #    """Make a new commit."""
    #    self.invoke_and_commit(message, user, lambda *a: True)

    def ismain(self):
        return self._revision.user_name() is None

    def shared(self):
        if self.ismain():
            return self
        return self._library.document(docid=self._revision.document_name())

    def take(self, user):
        fullid = self._library.fulldocid(self.id, user)

        def take_action(library, resolve):
            # branch from latest 
            library._create_branch(fullid, parent=self._revision)            

        if not self._library.has_revision(fullid):
            self.invoke_and_commit(take_action, \
                lambda d: ("$AUTO$ File checkout.", user) )

        return self._library.document_for_rev(fullid)
            
    def update(self, user):
        """Update parts of the document."""
        lock = self.library._lock()
        try:
            if self.ismain():
                # main revision of the document
                return True
            
            if self._revision.has_children():
                # can't update non-latest revision
                return False

            sv = self.shared()
            
            if not sv.ancestorof(self) and not self.parentof(sv):
                self._revision.merge_with(sv._revision, user=user)

            return True
        finally:
            lock.release()  

    def share(self, message):
        lock = self.library._lock()
        try:            
            if self.ismain():
                return True # always shared          

            user = self._revision.user_name()

            main = self.shared()._revision
            local = self._revision

            no_changes = True

            # Case 1:
            #         * local
            #         |
            #         * <- can also be here!
            #        /|
            #       / |
            # main *  *
            #      |  |
            # The local branch has been recently updated,
            # so we don't need to update yet again, but we need to
            # merge down to default branch, even if there was
            # no commit's since last update

            if main.ancestorof(local):
                print "case 1"
                main.merge_with(local, user=user, message=message)
                no_changes = False
            # Case 2:
            #
            # main *  * local
            #      |\ |
            #      | \|
            #      |  *
            #      |  |
            #
            # Default has no changes, to update from this branch
            # since the last merge of local to default.
            elif local.has_common_ancestor(main):
                print "case 2"
                if not local.parentof(main):
                    main.merge_with(local, user=user, message=message)
                    no_changes = False

            # Case 3:
            # main *
            #      |
            #      * <- this case overlaps with previos one
            #      |\
            #      | \
            #      |  * local
            #      |  |
            #
            # There was a recent merge to the defaul branch and
            # no changes to local branch recently.
            #
            # Use the fact, that user is prepared to see changes, to
            # update his branch if there are any
            elif local.ancestorof(main):
                print "case 3"
                if not local.parentof(main):
                    local.merge_with(main, user=user, message='Local branch update.')
                    no_changes = False
            else:
                print "case 4"
                local.merge_with(main, user=user, message='Local branch update.')
                local = self.shelf()
                main.merge_with(local, user=user, message=message)

            print "no_changes: ", no_changes
            return no_changes
        finally:
            lock.release()     

    def __str__(self):
        return u"Document(%s:%s)" % (self.name, self.owner)

    def __eq__(self, other):
        return (self._revision == other._revision) and (self.name == other.name)
