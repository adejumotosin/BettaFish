"""
RSS Feed Fetcher - No API keys required
Fetches content from RSS feeds and parses them
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSSFeedFetcher:
    """Fetch and parse RSS feeds from global news sources"""
    
    def __init__(self, user_agent="BettaFish/1.0"):
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
    def fetch_feed(self, feed_url: str, max_entries: int = 50) -> List[Dict]:
        """Fetch and parse a single RSS feed"""
        try:
            logger.info(f"Fetching feed: {feed_url}")
            
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            entries = []
            for entry in feed.entries[:max_entries]:
                parsed_entry = self._parse_entry(entry, feed_url)
                if parsed_entry:
                    entries.append(parsed_entry)
            
            logger.info(f"Successfully fetched {len(entries)} entries from {feed_url}")
            return entries
            
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {str(e)}")
            return []
    
    def _parse_entry(self, entry, feed_url: str) -> Optional[Dict]:
        """Parse a single feed entry into standardized format"""
        try:
            # Extract publication date
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])
            else:
                pub_date = datetime.now()
            
            # Extract content
            content = ""
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value
            elif hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            
            # Clean HTML from content
            content = self._clean_html(content)
            
            # Extract title
            title = entry.title if hasattr(entry, 'title') else "No Title"
            
            # Extract link
            link = entry.link if hasattr(entry, 'link') else feed_url
            
            # Extract author
            author = entry.author if hasattr(entry, 'author') else "Unknown"
            
            # Extract tags/categories
            tags = []
            if hasattr(entry, 'tags'):
                tags = [tag.term for tag in entry.tags]
            
            return {
                'title': title,
                'content': content,
                'link': link,
                'published_date': pub_date,
                'author': author,
                'tags': tags,
                'source_url': feed_url,
                'fetched_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error parsing entry: {str(e)}")
            return None
    
    def _clean_html(self, html_content: str) -> str:
        """Remove HTML tags and clean text"""
        if not html_content:
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error cleaning HTML: {str(e)}")
            return html_content
    
    def fetch_multiple_feeds(self, feed_urls: List[str], max_entries_per_feed: int = 30) -> List[Dict]:
        """Fetch multiple RSS feeds"""
        all_entries = []
        
        for feed_url in feed_urls:
            entries = self.fetch_feed(feed_url, max_entries_per_feed)
            all_entries.extend(entries)
            time.sleep(1)
        
        all_entries.sort(key=lambda x: x['published_date'], reverse=True)
        
        return all_entries