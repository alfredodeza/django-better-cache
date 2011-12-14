from bettercache.utils import CachingMixin, strip_wsgi
from bettercache.tasks import GeneratePage
from bettercache.proxy import proxy

import logging
logger = logging.getLogger()

class BetterView(CachingMixin):
    def get(self, request):
        response = None
        #should this bypass this replicates part of the irule
        if not self.should_bypass_cache(request):
            response, expired = self.get_cache(request)
            # send off the celery task if it's expired
            if expired:
                GeneratePage.apply_async((strip_wsgi(request),))
                self.set_cache(request, response)

        # if response is still none we have to proxy
        if response is None:
            logger.info('request %s proxied' %request.build_absolute_uri)
            response = proxy(request)
            #TODO: delete the following two lines
            #self.set_cache(request, response)
            response['X-Bettercache-Proxy'] = 'true'
        else:
            logger.info('request %s from cache' %request.build_absolute_uri)


        return response


#TODO: properly implement a class based view
BV = BetterView()
cache_view = BV.get
