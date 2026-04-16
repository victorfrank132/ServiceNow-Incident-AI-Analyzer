# Incident Deduplication System - Implementation Summary

## Problem Solved
The agent was re-analyzing the same incidents every 5 minutes and posting duplicate analysis comments to ServiceNow, creating excessive noise and clutter.

**Example of the issue:**
- Cycle 1: Post comment "Database issue - connection pool exhausted"
- Cycle 2: Post duplicate comment "Database issue - connection pool exhausted" 
- Cycle 3: Post another duplicate...
- Cycle N: Endless duplicate comments

## Solution Implemented

### 1. **Analysis Cache System**
- **File**: `logs/analyzed_incidents.json`
- **Purpose**: Tracks all previously analyzed incidents with their confidence scores
- **Format**: 
```json
{
  "INC0001111": {
    "confidence": 85,
    "category": "Database",
    "root_cause": "Connection pool exhausted",
    "timestamp": 1711502421.5
  }
}
```

### 2. **Smart Comment Posting Logic**
Added new method `_is_incident_already_analyzed()` that:
- Checks if incident was analyzed before
- Allows comment posting if confidence changed by >10 points (significant change)
- Skips comment if confidence within ±10 points (considered same analysis)

**Example:**
- First run: 85% confidence → POST comment
- Second run: 85% confidence → SKIP (same)
- Third run: 75% confidence → POST comment (confidence dropped 10 points - significant change!)
- Fourth run: 76% confidence → SKIP (within ±10 of previous)

### 3. **Updated Processing Summary**
New metrics show comment handling:

**Before:**
```
Total Processed: 10
Reassigned: 2
```

**After:**
```
Total Processed: 10
Successful Analyses: 10
  └─ Comments Posted: 2 (New/Updated)
  └─ Comments Skipped: 8 (Already analyzed)
Reassigned: 2
```

### 4. **Per-Incident Tracking**
Processing summary shows which incidents had comments posted vs skipped:

```
✓ INC0001111 [New]: Confidence 85% 💬 COMMENT ↗ REASSIGNED
✓ INC0001112 [New]: Confidence 82%            ↗ REASSIGNED
✓ INC0001113 [New]: Confidence 78%                        
```

Legend:
- `💬 COMMENT` = Comment posted (first time or confidence change)
- (empty) = Comment skipped (already analyzed)

## Technical Details

### Modified Files

#### `src/incident_processor.py`
1. **New imports:**
   - `json` - For cache serialization
   - `Path` from `pathlib` - For file operations

2. **New methods in IncidentProcessor class:**
   - `_load_analysis_cache()` - Load cached analyses from disk
   - `_save_analysis_cache()` - Persist cache to JSON file
   - `_is_incident_already_analyzed()` - Check if need to post comment
   - `_update_analysis_cache()` - Update cache with new analysis

3. **Modified methods:**
   - `__init__()` - Initialize analysis cache on startup
   - `process_incidents()` - Track comments_posted and comments_skipped
   - `process_single_incident()` - Check cache before posting comment
   - `get_processing_summary()` - Display comment statistics

### Cache Behavior

**Initialization:**
```python
# On startup, loads previous state if exists
self.analyzed_incidents = self._load_analysis_cache()
```

**Per-Incident Processing:**
```python
# Check if already analyzed
already_analyzed = self._is_incident_already_analyzed(incident_num, confidence)

if already_analyzed:
    # Skip comment posting
    logger.info(f"Skipping comment for {incident_num}")
else:
    # Post analysis comment
    comment_success = self.snow_client.add_comment_to_incident(...)
    result["comment_posted"] = True

# Always update cache with latest analysis
self._update_analysis_cache(incident_num, analysis)
```

**Cache Persistence:**
- Saved after every polling cycle
- JSON format for easy inspection
- Survives agent restarts (persists across runs)

## Benefits

1. **Reduced ServiceNow Clutter**: No more duplicate comments on incidents
2. **Smart Updates**: Comments post when confidence significantly changes (>10%)
3. **Persistent State**: Cache survives agent restarts - incidents won't be re-analyzed
4. **Observable**: Clear metrics showing comments posted vs skipped
5. **Configurable**: Threshold (currently 10% confidence change) can be adjusted

## Cache File Location
```
logs/analyzed_incidents.json
```

Example:
```json
{
  "INC0001111": {
    "confidence": 85,
    "category": "Database",
    "root_cause": "Connection pool exhausted",
    "timestamp": 1711502421.53
  },
  "INC0001112": {
    "confidence": 82,
    "category": "Application",
    "root_cause": "Memory leak detected",
    "timestamp": 1711502445.22
  }
}
```

## Testing

Run the deduplication test:
```bash
python3 test_deduplication.py
```

Expected output shows:
- **Cycle 1**: Comments Posted = 1, Comments Skipped = 0
- **Cycle 2**: Comments Posted = 0, Comments Skipped = 1 ✓
- **Cycle 3**: Comments Posted = 0, Comments Skipped = 1 ✓

## Configuration

**To adjust deduplication sensitivity**, modify in `src/incident_processor.py`:
```python
def _is_incident_already_analyzed(self, incident_num: str, current_confidence: int) -> bool:
    # Change this value to adjust sensitivity (currently ±10 points)
    return abs(current_confidence - cached_confidence) <= 10
```

- Smaller value (e.g., 5) = More sensitive to confidence changes
- Larger value (e.g., 15) = Less sensitive, fewer comment updates

## Future Enhancements

1. Add confidence trend tracking (show analysis is improving/degrading)
2. Manual cache reset via API endpoint
3. Configurable comment frequency via config file
4. Archive old analyses (remove from cache after 7 days)
5. Dashboard showing deduplication stats
