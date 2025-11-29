"""
Global Data Collector
Collects data from RSS feeds and web scraping, stores in database
"""

import sys
import os
import json
from datetime import datetime
import logging
from typing import List, Dict

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from rss_feeds import get_all_feeds
from rss_fetcher import RSSFeedFetcher
from web_scraper import GlobalWebScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GlobalDataCollector:
    """Main class for collecting global data"""
    
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.rss_fetcher = RSSFeedFetcher()
        self.web_scraper = GlobalWebScraper(headless=True)
        
    def collect_rss_feeds(self, max_entries_per_feed: int = 30):
        """Collect data from all configured RSS feeds"""
        logger.info("Starting RSS feed collection...")
        
        all_feeds = get_all_feeds()
        total_collected = 0
        
        for feed_info in all_feeds:
            try:
                logger.info(f"Fetching feed: {feed_info['source']} - {feed_info['category']}")
                
                entries = self.rss_fetcher.fetch_feed(
                    feed_info['url'], 
                    max_entries=max_entries_per_feed
                )
                
                for entry in entries:
                    entry['language'] = feed_info['language']
                    entry['region'] = feed_info['region']
                    entry['source'] = feed_info['source']
                    entry['category'] = feed_info['category']
                    entry['platform'] = 'rss'
                
                saved_count = self._save_content_batch(entries)
                total_collected += saved_count
                
                logger.info(f"Saved {saved_count} entries from {feed_info['source']}")
                
            except Exception as e:
                logger.error(f"Error collecting feed {feed_info['url']}: {str(e)}")
                continue
        
        logger.info(f"RSS collection completed. Total items collected: {total_collected}")
        return total_collected
    
    def collect_reddit(self, subreddits: List[str] = None, max_posts: int = 50):
        """Collect data from Reddit"""
        if subreddits is None:
            subreddits = ['worldnews', 'news', 'technology']

        logger.info(f"Starting Reddit collection from {len(subreddits)} subreddits...")
        total_collected = 0

        for subreddit in subreddits:
            try:
                logger.info(f"Scraping r/{subreddit}...")
                posts = self.web_scraper.scrape_reddit(subreddit, max_posts=max_posts)

                standardized = []
                for post in posts:
                    score = self._parse_reddit_score(post.get('score', '0'))

                    standardized.append({
                        'platform': 'reddit',
                        'source': f'reddit_r/{subreddit}',
                        'title': post['title'],
                        'content': post['title'],
                        'url': post['link'],
                        'author': post['author'],
                        'published_date': post.get('posted_time'),
                        'comments_count': post['comments_count'],
                        'likes': score,
                        'language': 'en',
                        'region': 'global',
                        'category': subreddit,
                        'metadata': {'subreddit': subreddit}
                    })

                saved_count = self._save_content_batch(standardized)
                total_collected += saved_count

                logger.info(f"Saved {saved_count} posts from r/{subreddit}")

            except Exception as e:
                logger.error(f"Error collecting Reddit r/{subreddit}: {str(e)}")
                continue

        logger.info(f"Reddit collection completed. Total items collected: {total_collected}")
        return total_collected

    def _parse_reddit_score(self, score_text: str) -> int:
        """Convert Reddit score text to integer (handles '17.9k', '•', etc.)"""
        if not score_text or score_text == '•' or score_text == '':
            return 0
        
        try:
            # Remove any whitespace
            score_text = str(score_text).strip()
            
            # Handle 'k' notation (e.g., '17.9k' = 17900)
            if 'k' in score_text.lower():
                number = float(score_text.lower().replace('k', ''))
                return int(number * 1000)
            
            # Handle 'm' notation (e.g., '1.5m' = 1500000)
            if 'm' in score_text.lower():
                number = float(score_text.lower().replace('m', ''))
                return int(number * 1000000)
            
            # Try to convert directly to int
            return int(float(score_text))
            
        except (ValueError, AttributeError):
            # If all else fails, return 0
            return 0

    def _save_content_batch(self, entries: List[Dict]) -> int:
        """Save a batch of content entries to database"""
        if not entries:
            return 0
        
        session = self.Session()
        saved_count = 0
        
        try:
            for entry in entries:
                try:
                    url = entry.get('url')
                    if url:
                        result = session.execute(
                            text("SELECT id FROM global_content WHERE url = :url"),
                            {"url": url}
                        )
                        if result.fetchone():
                            continue
                    
                    # Fixed INSERT query with proper JSONB casting
                    insert_query = text("""
                        INSERT INTO global_content 
                        (platform, source, title, content, url, author, published_date,
                         language, region, category, likes, shares, comments_count, metadata)
                        VALUES 
                        (:platform, :source, :title, :content, :url, :author, :published_date,
                         :language, :region, :category, :likes, :shares, :comments_count, 
                         CAST(:metadata AS jsonb))
                    """)
                    
                    # Convert metadata to JSON string
                    metadata_str = json.dumps(entry.get('metadata', {}))
                    
                    data = {
                        'platform': entry.get('platform', 'unknown'),
                        'source': entry.get('source', 'unknown'),
                        'title': entry.get('title', '')[:1000],
                        'content': entry.get('content', '')[:50000],
                        'url': entry.get('url', ''),
                        'author': entry.get('author', 'Unknown')[:200],
                        'published_date': entry.get('published_date'),
                        'language': entry.get('language', 'en'),
                        'region': entry.get('region', 'global'),
                        'category': entry.get('category', 'general'),
                        'likes': entry.get('likes', 0),
                        'shares': entry.get('shares', 0),
                        'comments_count': entry.get('comments_count', 0),
                        'metadata': metadata_str
                    }
                    
                    session.execute(insert_query, data)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving entry: {str(e)}")
                    continue
            
            session.commit()
            logger.info(f"Successfully saved {saved_count}/{len(entries)} entries")
            
        except Exception as e:
            logger.error(f"Error in batch save: {str(e)}")
            session.rollback()
        finally:
            session.close()
        
        return saved_count

    def run_full_collection(self):
        """Run full data collection from all sources"""
        logger.info("=" * 50)
        logger.info("Starting FULL data collection...")
        logger.info("=" * 50)
        
        total_items = 0
        
        logger.info("\n--- Phase 1: RSS Feeds ---")
        rss_count = self.collect_rss_feeds(max_entries_per_feed=30)
        total_items += rss_count
        
        logger.info("\n--- Phase 2: Reddit ---")
        reddit_count = self.collect_reddit(
            subreddits=['worldnews', 'news', 'technology'],
            max_posts=30
        )
        total_items += reddit_count
        
        logger.info("=" * 50)
        logger.info(f"COLLECTION COMPLETED!")
        logger.info(f"Total items collected: {total_items}")
        logger.info(f"- RSS: {rss_count}")
        logger.info(f"- Reddit: {reddit_count}")
        logger.info("=" * 50)
        
        return total_items


def main():
    """Main function"""
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    DB_USER = 'postgres'
    DB_PASSWORD = 'bettafish'
    DB_NAME = 'bettafish_global'
    
    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    collector = GlobalDataCollector(db_url)
    collector.run_full_collection()


if __name__ == "__main__":
    main()
