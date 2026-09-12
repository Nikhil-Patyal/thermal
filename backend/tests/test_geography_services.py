import pytest
from unittest.mock import patch
from geography.services import GeographyService

def test_haversine():
    from geography.services import haversine
    assert haversine(10, 10, 10, 10) == 0.0

@patch('geography.services.requests.post')
@patch('geography.services.GeographyCache.get', return_value=None)
@patch('geography.services.GeographyCache.set')
def test_overpass_infrastructure_success(mock_cache_set, mock_cache_get, mock_post):
    class MockResponse:
        status_code = 200
        def json(self):
            return {
                "elements": [
                    {"type": "node", "id": 1, "lat": 10.001, "lon": 10.001, "tags": {"landuse": "industrial"}}
                ]
            }
    mock_post.return_value = MockResponse()
    
    res = GeographyService.get_overpass_infrastructure(10.0, 10.0, 1000)
    assert res['source_available'] is True
    assert res['industrial_count'] == 1
    assert res['distance_to_industry'] is not None

@patch('geography.services.requests.post')
@patch('geography.services.GeographyCache.get', return_value=None)
def test_overpass_infrastructure_failure(mock_cache_get, mock_post):
    class MockResponse:
        status_code = 500
    mock_post.return_value = MockResponse()
    
    res = GeographyService.get_overpass_infrastructure(10.0, 10.0, 1000)
    assert res['source_available'] is False
    assert res['industrial_count'] is None

@patch('geography.services.requests.get')
@patch('geography.services.GeographyCache.get', return_value=None)
def test_copernicus_land_cover_success(mock_cache_get, mock_get):
    GeographyService.COPERNICUS_API_KEY = "dummy"
    class MockResponse:
        status_code = 200
        def json(self):
            return {
                "forest_fraction": 0.5,
                "cropland_fraction": 0.2,
                "builtup_fraction": 0.1
            }
    mock_get.return_value = MockResponse()
    
    res = GeographyService.get_copernicus_land_cover(10.0, 10.0, 1000)
    assert res['source_available'] is True
    assert res['forest_fraction'] == 0.5
    
def test_extract_context_features():
    res = GeographyService.extract_context_features(10.0, 10.0)
    assert isinstance(res, dict)
