# -*- coding: utf-8 -*-
"""
@author: Blacklistede
"""
import requests
import random
import time
import argparse


class HashTagResearch():
    
    def __init__(self):
        self.s                  = requests.Session()
#        self.s.verify           = False
        self.browser_headers    = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                                   'Host': 'www.instagram.com',
                                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                   'Upgrade-Insecure-Requests': '1'}
        
        self.request_headers    = {'User-Agent'         : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                                   'X-Instagram-AJAX'   : '1',
                                   'X-CSRFToken'        : 'csrftoken',
                                   'Origin'             : 'https://www.instagram.com',
                                   'Referer'            : 'https://www.instagram.com'}
                                   
        self.explore_headers    = {'Host'               : 'www.instagram.com',
                                   'User-Agent'         : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0',
                                   'Accept'             : '*/*',
                                   'Accept-Language'    : 'en-US;q=0.7,en;q=0.3',
                                   'Accept-Encoding'    : 'gzip, deflate, br',
                                   'X-Requested-With'   : 'XMLHttpRequest',
                                   'Referer'            : 'https://www.instagram.com/',
                                   'Connection'         : 'keep-alive'}

        self.s.headers          = self.browser_headers
        self.base_url           = 'https://www.instagram.com/'
        self.query_url          = self.base_url + 'query/'
        self.login_url          = self.base_url + 'accounts/login/ajax/'
        self.search_url         = self.base_url + 'web/search/topsearch/'
        self.explore_url        = self.base_url + 'explore/tags/'
        
    def post_request(self, url, data, **kwargs):
        """Make a POST request"""
        request = self.s.post(url, data = data, **kwargs)
        return self.analyze_request(request)
        
    def get_request(self, url, params = None, **kwargs):
        """Make a GET request"""
        request = self.s.get(url, params = params, **kwargs)
        return self.analyze_request(request)
        
    def analyze_request(self, request):
        """Check if the request was successful"""
        if request.status_code == 200:
            return request
        else:
            raise requests.HTTPError(str(request.status_code))
        
    def setup_session(self):
        """Go to instagram.com to fetch crsf token and session cookies"""
        self.get_request(self.base_url)
        self.request_headers['X-CSRFToken'] = self.s.cookies.get_dict()['csrftoken']
        
    def login(self, username, password):
        """Login to Instagram account. Required to explore hashtags"""
        payload     = {'username': username,
                       'password': password}
        response    = self.post_request(self.login_url, data = payload, headers = self.request_headers).json()
        if response['status'] == 'ok' and response['authenticated']:
            return True
        else:
            print(response)
            raise Exception('Failed to login')
    
    def explore_hashtags(self, hashtag, min_posts = None, max_posts = None):
        """Get recommended hashtags based on a hashtag. Takes a string, returns a list"""
        if hashtag[0] != '#':
            hashtag = '#' + hashtag
        params      = {'context'     : 'blended',
                       'query'       : hashtag,
                       'rank_token'  : random.uniform(0, 1)}
        response    = self.get_request(self.search_url, params = params, headers = self.explore_headers)
        tag_list    = response.json()['hashtags']
        tags        = []
        for tag in tag_list:
            if min_posts:
                if tag['hashtag']['media_count'] < min_posts:
                    continue
            if max_posts:
                if tag['hashtag']['media_count'] > max_posts:
                    continue
            tags.append(tag['hashtag']['name'])
        return tags
        
    def trim_hashtags(self, hashtags, amount):
        """Returns a list with the first x items"""
        return hashtags[:amount]
    
    def get_hashtag_info(self, hashtag):
        """Get the posts of a hashtag and the like/comment range of the popular pictures"""
        url         = self.explore_url + str(hashtag) + '/'
        params      = {'__a': 1}
        response    = self.get_request(url, params = params).json()
        post_amount = response['graphql']['hashtag']['edge_hashtag_to_media']['count']
        top_posts   = response['graphql']['hashtag']['edge_hashtag_to_top_posts']['edges']
        """Get min/max comments/likes"""
        min_likes, min_comments = 9999999999999, 9999999999999 #very big number, just temporary
        max_likes, max_comments = 0, 0
        for post in top_posts:
            likes       = post['node']['edge_liked_by']['count']
            comments    = post['node']['edge_media_to_comment']['count']
            if likes < min_likes:
                min_likes = likes
            if likes > max_likes:
                max_likes = likes
            if comments < min_comments:
                min_comments = comments
            if comments > max_comments:
                max_comments = comments
        hashtag_info = {'name'          : hashtag,
                        'post_amount'   : post_amount,
                        'min_likes'     : min_likes,
                        'max_likes'     : max_likes,
                        'min_comments'  : min_comments,
                        'max_comments'  : max_comments}
        return hashtag_info
        

def main(username, password, hashtags, max_hashtags = None, min_posts = None, max_posts = None, suggestions = True, file = False):
    htr = HashTagResearch()
    """Setup"""
    htr.setup_session()
    htr.login(username, password)
    if file:
        """ Read file into list """
        with open(file) as f:
            hashtags = f.read().splitlines()
    """Get suggested hashtags"""
    hashtag_list = []
    if suggestions:
        for tag in hashtags:
            print('Getting suggested hashtags for ' + str(str(tag).encode()))
            try:
                new_tags = htr.explore_hashtags(tag, min_posts = min_posts, max_posts = max_posts)
                """Cut list if max_hashtags are set"""
                if max_hashtags:
                    new_tags = htr.trim_hashtags(new_tags, max_hashtags)
                """Add tags to hashtag list to be analyzed later"""
                hashtag_list.extend(new_tags)
            except Exception as ex:
                print(ex)
                print('Error fetching recommended hashtags for ' + str(tag))
            time.sleep(1.5)
    else:
        hashtag_list = hashtags
    """Remove duplicates"""
    hashtag_list    = list(set(hashtag_list))
    """Analyze hashtags"""
    hashtag_infos   = []
    for tag in hashtag_list:
        print('Getting infos for ' + str(str(tag).encode()))
        try:
            tag_info = htr.get_hashtag_info(tag)
            hashtag_infos.append(tag_info)
        except Exception as ex:
            print(ex)
            print('Failed to get informations for ' + str(str(tag).encode()))
            error    = 'ERROR'
            tag_info = {'name'          : str(str(tag).encode()),
                        'post_amount'   : error,
                        'min_likes'     : error,
                        'max_likes'     : error,
                        'min_comments'  : error,
                        'max_comments'  : error}
            hashtag_infos.append(tag_info)
        """Security delay"""
        time.sleep(1.5)
    """Write to file"""
    with open('hashtaginfo.csv', 'w+', encoding = 'utf-8') as file:
        """Legend"""
        print('Writing to file...')
        file.write('HASHTAG,POST AMOUNT,MIN LIKES, MAX LIKES, MIN COMMENTS, MAX COMMENTS\n')
        for info in hashtag_infos:
            file.write(str(info['name'])            + ',' +
                       str(info['post_amount'])     + ',' +
                       str(info['min_likes'])       + ',' + 
                       str(info['max_likes'])       + ',' + 
                       str(info['min_comments'])    + ',' + 
                       str(info['max_comments'])    + '\n')
        print('Scraped ' + str(len(hashtag_infos)) + ' tags!')
        print('DONE!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username', help = 'Your IG username')
    parser.add_argument('password', help = 'Your IG password')
    parser.add_argument('hashtags', help = 'The hashtags you want to analyze. Seperate by comma. Example: car,boat,plane')
    parser.add_argument('--max_tags', help = 'The maximum of suggested tags to fetch per hashtag', type = int)
    parser.add_argument('--min_posts', help = 'Check only tags with minimum posts', type = int)
    parser.add_argument('--max_posts', help = 'Check only tags with maximum posts', type = int)
    parser.add_argument('--nosuggestions', help = 'Don\'t get suggestions for the inputted hashtags', dest = 'suggestions', action = 'store_false')
    parser.add_argument('--file', help = 'You need this flag if you are using a .txt file to import hashtags.', dest = 'file', action = 'store_true')
    parser.set_defaults(suggestions = True, file = False)
    args = parser.parse_args()
    if not args.file:
        hashtags = list(filter(None, args.hashtags.split(','))) #Create list and remove empty elements  
    else:
        hashtags = []
    if args.file:
        file = args.hashtags
    else:
        file = False
    main(args.username, args.password, hashtags, args.max_tags, args.min_posts, args.max_posts, args.suggestions, file)