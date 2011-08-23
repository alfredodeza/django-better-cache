from bettercache.tasks import GeneratePage
from bettercache.utils import CachingMixin


class TestAsyncMiddleware(object):
    """ Does not deal with middleware sideeffects """
    def process_request(self, request):
        response = GeneratePage().run(request)
        return response


class BetterCacheMiddleware(CachingMixin):
    def process_request(self, request):
        """
        Checks whether the page is already cached and returns the cached
        version if available.
        """
        if not request.method in ('GET', 'HEAD'):
            request._cache_update_cache = False
            return None # Don't bother checking the cache.

        response, expired = self.get_cache(request)
        request._cache_update_cache = True

        if response is None:
            return None # No cache information available, need to rebuild.

        # send off the task if we have to
        if expired:
            GeneratePage.apply_async(request)
        # don't update right since we're just serving from cache
        request._cache_update_cache = False

        return response

    def process_response(self, request, response):
        """ Sets the cache, if needed.
            Copied from django so headers are only updated when appropriate.
        """                                                                             
        if not self.should_cache(request, response):
            # We don't need to update the cache, just return.                                                        
            return response 

        response = self.patch_headers(response)
        self.set_cache()
        
        return response
