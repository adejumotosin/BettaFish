"""
Web Scraper for Social Media and News Sites
No API keys required - uses direct web scraping
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GlobalWebScraper:
    """Scrape content from various platforms without API keys"""
    
    def __init__(self, headless=True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.headless = headless
    
    def scrape_reddit(self, subreddit: str, max_posts: int = 50) -> List[Dict]:
        """Scrape Reddit without API using old.reddit.com"""
        try:
            url = f"https://old.reddit.com/r/{subreddit}/"
            logger.info(f"Scraping Reddit: {url}")
            
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            posts = []
            for post_div in soup.find_all('div', class_='thing', limit=max_posts):
                try:
                    title_element = post_div.find('a', class_='title')
                    if not title_element:
                        continue
                    
                    title = title_element.text.strip()
                    link = title_element.get('href', '')
                    if link.startswith('/r/'):
                        link = f"https://old.reddit.com{link}"
                    
                    score_element = post_div.find('div', class_='score unvoted')
                    score = score_element.text if score_element else '0'
                    
                    author_element = post_div.find('a', class_='author')
                    author = author_element.text if author_element else 'Unknown'
                    
                    comments_element = post_div.find('a', class_='comments')
                    comments_text = comments_element.text if comments_element else '0 comments'
                    comments_count = re.search(r'(\d+)', comments_text)
                    comments_count = int(comments_count.group(1)) if comments_count else 0
                    
                    time_element = post_div.find('time')
                    posted_time = time_element.get('datetime') if time_element else None
                    
                    posts.append({
                        'platform': 'reddit',
                        'title': title,
                        'link': link,
                        'author': author,
                        'score': score,
                        'comments_count': comments_count,
                        'posted_time': posted_time,
                        'subreddit': subreddit,
                        'scraped_at': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing Reddit post: {str(e)}")
                    continue
            
            logger.info(f"Scraped {len(posts)} posts from r/{subreddit}")
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping Reddit: {str(e)}")
            return []
    
    def scrape_twitter_nitter(self, username: str, max_tweets: int = 50) -> List[Dict]:
        """Scrape Twitter via Nitter (privacy-focused Twitter frontend)"""
        try:
            url = f"https://nitter.net/{username}"
            logger.info(f"Scraping Twitter via Nitter: {url}")
            
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            tweets = []
            tweet_divs = soup.find_all('div', class_='timeline-item', limit=max_tweets)
            
            for tweet_div in tweet_divs:
                try:
                    content_div = tweet_div.find('div', class_='tweet-content')
                    if not content_div:
                        continue
                    
                    content = content_div.get_text(strip=True)
                    
                    time_element = tweet_div.find('span', class_='tweet-date')
                    tweet_time = time_element.get('title') if time_element else None
                    
                    link_element = tweet_div.find('a', class_='tweet-link')
                    tweet_link = f"https://nitter.net{link_element.get('href')}" if link_element else ''
                    
                    tweets.append({
                        'platform': 'twitter',
                        'username': username,
                        'content': content,
                        'posted_time': tweet_time,
                        'link': tweet_link,
                        'scraped_at': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing tweet: {str(e)}")
                    continue
            
            logger.info(f"Scraped {len(tweets)} tweets from @{username}")
            return tweets
            
        except Exception as e:
            logger.error(f"Error scraping Twitter via Nitter: {str(e)}")
            return []