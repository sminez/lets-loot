'''
Base parser classes that turn equipment specs into in game classes that
can be used.
NOTE:: If this is to run under Kivy in the end then it will need to use
a compatable data store.
--> Trying sqlite for now.
'''


class ItemConsumed(Exception):
    pass


class Item:
    '''
    Base interface class for all items
    '''
    name = None
    slot = None

    def use(self, target=None):
        '''
        Use the item. Raises an ItemConsumed exception if the item can no
        longer be used after this
        '''
        raise NotImplementedError
