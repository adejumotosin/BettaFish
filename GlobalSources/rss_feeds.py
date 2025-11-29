"""
Global RSS Feeds Configuration
No API keys required - uses free RSS feeds from major news sources
"""

GLOBAL_RSS_FEEDS = {
    # English Language Sources
    'english': {
        'bbc': {
            'name': 'BBC News',
            'feeds': {
                'world': 'http://feeds.bbci.co.uk/news/world/rss.xml',
                'business': 'http://feeds.bbci.co.uk/news/business/rss.xml',
                'technology': 'http://feeds.bbci.co.uk/news/technology/rss.xml',
            },
            'region': 'uk',
            'language': 'en'
        },
        'guardian': {
            'name': 'The Guardian',
            'feeds': {
                'world': 'https://www.theguardian.com/world/rss',
                'business': 'https://www.theguardian.com/business/rss',
                'technology': 'https://www.theguardian.com/technology/rss',
            },
            'region': 'uk',
            'language': 'en'
        },
        'aljazeera': {
            'name': 'Al Jazeera English',
            'feeds': {
                'world': 'https://www.aljazeera.com/xml/rss/all.xml',
            },
            'region': 'middle_east',
            'language': 'en'
        },
        'techcrunch': {
            'name': 'TechCrunch',
            'feeds': {
                'technology': 'https://techcrunch.com/feed/',
            },
            'region': 'us',
            'language': 'en'
        },
        'hacker_news': {
            'name': 'Hacker News',
            'feeds': {
                'top': 'https://hnrss.org/frontpage',
            },
            'region': 'global',
            'language': 'en'
        }
    },
    
    # Reddit RSS (No API needed!)
    'reddit': {
        'popular': {
            'name': 'Reddit',
            'feeds': {
                'worldnews': 'https://www.reddit.com/r/worldnews/.rss',
                'news': 'https://www.reddit.com/r/news/.rss',
                'technology': 'https://www.reddit.com/r/technology/.rss',
                'business': 'https://www.reddit.com/r/business/.rss',
            },
            'region': 'global',
            'language': 'en'
        }
    }
}

def get_all_feeds():
    """Get all RSS feed URLs in a flat list"""
    all_feeds = []
    for language, sources in GLOBAL_RSS_FEEDS.items():
        for source_key, source_data in sources.items():
            for category, feed_url in source_data['feeds'].items():
                all_feeds.append({
                    'url': feed_url,
                    'source': source_data['name'],
                    'language': source_data['language'],
                    'region': source_data['region'],
                    'category': category
                })
    return all_feeds

def get_feeds_by_language(language_code):
    """Get feeds for a specific language"""
    if language_code in GLOBAL_RSS_FEEDS:
        return GLOBAL_RSS_FEEDS[language_code]
    return {}

def get_feeds_by_region(region):
    """Get feeds for a specific region"""
    region_feeds = []
    for language, sources in GLOBAL_RSS_FEEDS.items():
        for source_key, source_data in sources.items():
            if source_data['region'] == region or source_data['region'] == 'global':
                region_feeds.append(source_data)
    return region_feeds