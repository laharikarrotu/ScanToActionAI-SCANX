"""
Database Optimization Module - Query Optimization and Indexing
Provides database performance improvements and query optimization utilities
"""
from sqlalchemy import Index, text
from sqlalchemy.engine import Engine
from typing import List, Dict, Any
import logging

from .database import engine, Base
from core.logger import get_logger

logger = get_logger("database.optimization")


class DatabaseOptimizer:
    """
    Database optimization utilities for better query performance
    Creates indexes, optimizes queries, and provides performance monitoring
    """
    
    def __init__(self, db_engine: Engine = None):
        """
        Initialize database optimizer
        
        Args:
            db_engine: SQLAlchemy engine (defaults to global engine)
        """
        self.engine = db_engine or engine
        self.logger = logger
    
    def create_indexes(self) -> List[str]:
        """
        Create performance indexes for common queries
        
        Returns:
            List of created index names
        """
        created_indexes = []
        
        try:
            # Indexes for ScanRequest table
            indexes = [
                # Index on session_id for faster session lookups
                Index('idx_scan_request_session_id', 'scan_request.session_id'),
                
                # Index on image_hash for faster duplicate detection
                Index('idx_scan_request_image_hash', 'scan_request.image_hash'),
                
                # Index on created_at for time-based queries
                Index('idx_scan_request_created_at', 'scan_request.created_at'),
                
                # Composite index for common query pattern
                Index('idx_scan_request_session_created', 'scan_request.session_id', 'scan_request.created_at'),
            ]
            
            for index in indexes:
                try:
                    index.create(self.engine)
                    created_indexes.append(index.name)
                    self.logger.info(f"Created index: {index.name}")
                except Exception as e:
                    self.logger.warning(f"Index {index.name} may already exist: {e}")
            
            self.logger.info(f"Created {len(created_indexes)} indexes")
            return created_indexes
            
        except Exception as e:
            self.logger.error("Failed to create indexes", exception=e)
            return created_indexes
    
    def analyze_tables(self) -> Dict[str, Any]:
        """
        Analyze database tables for optimization opportunities
        
        Returns:
            Dictionary with table statistics and recommendations
        """
        analysis = {}
        
        try:
            with self.engine.connect() as conn:
                # Get table statistics
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_live_tup as row_count,
                        n_dead_tup as dead_rows,
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC
                """))
                
                tables = []
                for row in result:
                    tables.append({
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "row_count": row.row_count,
                        "dead_rows": row.dead_rows,
                        "last_vacuum": str(row.last_vacuum) if row.last_vacuum else None,
                        "last_analyze": str(row.last_analyze) if row.last_analyze else None
                    })
                
                analysis["tables"] = tables
                
                # Get index usage statistics
                index_result = conn.execute(text("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan as index_scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes
                    WHERE idx_scan = 0
                    ORDER BY tablename
                """))
                
                unused_indexes = []
                for row in index_result:
                    unused_indexes.append({
                        "table": row.tablename,
                        "index": row.indexname,
                        "scans": row.index_scans
                    })
                
                analysis["unused_indexes"] = unused_indexes
                analysis["recommendations"] = self._generate_recommendations(analysis)
                
        except Exception as e:
            self.logger.error("Failed to analyze tables", exception=e)
            analysis["error"] = str(e)
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate optimization recommendations based on analysis
        
        Args:
            analysis: Table analysis results
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check for tables with many dead rows
        for table in analysis.get("tables", []):
            if table.get("dead_rows", 0) > 1000:
                recommendations.append(
                    f"Table {table['table']} has {table['dead_rows']} dead rows. "
                    "Consider running VACUUM."
                )
            
            # Check for tables that haven't been analyzed recently
            if not table.get("last_analyze"):
                recommendations.append(
                    f"Table {table['table']} has never been analyzed. "
                    "Run ANALYZE to update statistics."
                )
        
        # Check for unused indexes
        unused_count = len(analysis.get("unused_indexes", []))
        if unused_count > 0:
            recommendations.append(
                f"Found {unused_count} unused indexes. "
                "Consider removing them to improve write performance."
            )
        
        return recommendations
    
    def optimize_queries(self) -> Dict[str, Any]:
        """
        Run query optimization tasks
        
        Returns:
            Dictionary with optimization results
        """
        results = {
            "indexes_created": [],
            "vacuum_run": False,
            "analyze_run": False
        }
        
        try:
            # Create indexes
            results["indexes_created"] = self.create_indexes()
            
            # Run VACUUM (if needed)
            with self.engine.connect() as conn:
                conn.execute(text("VACUUM ANALYZE"))
                conn.commit()
                results["vacuum_run"] = True
                results["analyze_run"] = True
                self.logger.info("Ran VACUUM ANALYZE")
            
        except Exception as e:
            self.logger.error("Query optimization failed", exception=e)
            results["error"] = str(e)
        
        return results


def optimize_database():
    """
    Convenience function to optimize database
    
    Returns:
        Optimization results
    """
    optimizer = DatabaseOptimizer()
    return optimizer.optimize_queries()

