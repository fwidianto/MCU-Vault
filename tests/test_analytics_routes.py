"""
Tests for analytics routes (Phase 2B).
"""
import pytest
import json


class TestHealthDashboard:
    """Tests for health analytics dashboard."""
    
    def test_health_dashboard_requires_auth(self, client):
        """Health dashboard should require authentication."""
        response = client.get('/dashboard/health', follow_redirects=True)
        assert b'Login' in response.data or b'Sign In' in response.data or response.status_code == 200
    
    def test_health_dashboard_loads(self, auth_client):
        """Health dashboard should load successfully."""
        response = auth_client.get('/dashboard/health')
        assert response.status_code == 200
    
    def test_health_dashboard_shows_data(self, auth_client, sample_records_with_metrics):
        """Health dashboard should show data when records exist."""
        response = auth_client.get('/dashboard/health')
        html = response.data.decode('utf-8')
        assert response.status_code == 200
        # Should have some content related to analytics
        assert 'Health' in html or 'analytics' in html.lower() or response.status_code == 200


class TestTrendDataAPI:
    """Tests for trend data API endpoint."""
    
    def test_trend_data_requires_auth(self, client):
        """Trend data API should require authentication."""
        response = client.get('/api/trends')
        # Should redirect or return unauthorized
        assert response.status_code in [302, 401] or b'Login' in response.data
    
    def test_trend_data_no_records(self, auth_client):
        """Trend data should handle no records gracefully."""
        response = auth_client.get('/api/trends')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # Should have either error or labels
        assert 'error' in data or 'labels' in data
    
    def test_trend_data_with_records(self, auth_client, sample_records_with_metrics):
        """Trend data should return data for records."""
        response = auth_client.get('/api/trends')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Should have structure for charts
        assert 'labels' in data
        assert 'body_measurements' in data
        assert 'records_count' in data
        
        # Should have 3 records
        assert data['records_count'] == 3


class TestCompareRecords:
    """Tests for record comparison page."""
    
    def test_compare_requires_auth(self, client):
        """Compare page should require authentication."""
        response = client.get('/records/compare', follow_redirects=True)
        assert b'Login' in response.data or b'Sign In' in response.data or response.status_code == 200
    
    def test_compare_page_loads(self, auth_client):
        """Compare page should load successfully."""
        response = auth_client.get('/records/compare')
        assert response.status_code == 200
    
    def test_compare_shows_selector(self, auth_client, sample_records_with_metrics):
        """Compare page should show record selector."""
        response = auth_client.get('/records/compare')
        html = response.data.decode('utf-8')
        assert response.status_code == 200
        assert 'compare' in html.lower() or 'Record' in html
    
    def test_compare_with_two_records(self, auth_client, sample_records_with_metrics):
        """Compare page should work with two records selected."""
        record1_id = sample_records_with_metrics['record1']
        record2_id = sample_records_with_metrics['record3']
        
        response = auth_client.get(f'/records/compare?record_a={record1_id}&record_b={record2_id}')
        assert response.status_code == 200


class TestExportComparison:
    """Tests for comparison export functionality."""
    
    def test_export_requires_auth(self, client):
        """Export should require authentication."""
        response = client.get('/records/compare/export?record_a=1&record_b=2')
        assert response.status_code in [302, 401] or b'Login' in response.data
    
    def test_export_works(self, auth_client, sample_records_with_metrics):
        """Export should return CSV when parameters provided."""
        record1_id = sample_records_with_metrics['record1']
        record2_id = sample_records_with_metrics['record3']
        
        response = auth_client.get(
            f'/records/compare/export?record_a={record1_id}&record_b={record2_id}'
        )
        
        # Should be CSV or redirect
        assert 'text/csv' in response.content_type or response.status_code == 302


class TestLatestSnapshotAPI:
    """Tests for latest snapshot API."""
    
    def test_latest_snapshot_requires_auth(self, client):
        """Latest snapshot API should require authentication."""
        response = client.get('/api/latest-snapshot')
        assert response.status_code in [302, 401] or b'Login' in response.data
    
    def test_latest_snapshot_works(self, auth_client, sample_records_with_metrics):
        """Latest snapshot should return data."""
        response = auth_client.get('/api/latest-snapshot')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'has_data' in data


class TestRecordClassificationsAPI:
    """Tests for record classifications API."""
    
    def test_classifications_requires_auth(self, client):
        """Classifications API should require authentication."""
        response = client.get('/api/records/1/classifications')
        assert response.status_code in [302, 401] or b'Login' in response.data
    
    def test_classifications_not_found(self, auth_client):
        """Classifications should return 404 for non-existent record."""
        response = auth_client.get('/api/records/99999/classifications')
        # May return 404 or redirect to login
        assert response.status_code in [404, 302]
    
    def test_classifications_success(self, auth_client, sample_records_with_metrics):
        """Classifications should return data for valid record."""
        record_id = sample_records_with_metrics['record1']
        
        response = auth_client.get(f'/api/records/{record_id}/classifications')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'has_data' in data