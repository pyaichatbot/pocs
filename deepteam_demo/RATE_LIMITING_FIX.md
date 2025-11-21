# Rate Limiting and Code Fixes

## Issues Identified

### 1. Rate Limiting (429 Errors)
**Problem:** Anthropic API was returning 429 "Too Many Requests" errors due to exceeding concurrent connection limits.

**Root Cause:** `max_concurrent=10` was too high for Anthropic's rate limits. Anthropic has strict limits on concurrent connections.

**Solution:**
- Reduced `max_concurrent` default from `10` to `3` in `config/settings.py`
- Updated README.md to reflect the new default
- Added documentation explaining the rate limit constraint

### 2. Tuple Return Issue
**Problem:** `model.a_generate()` returns a tuple `(text, cost)`, but code was treating it as a string, causing "unable to render tuple" errors.

**Root Cause:** DeepEval's `a_generate()` method returns `Tuple[str, float]` (text and cost), not just a string.

**Solution:**
- Fixed all model callbacks in:
  - `apps/simple_model_app.py`
  - `apps/rag_app.py`
  - `apps/chatbot_app.py`
  - `apps/agent_app.py`
- Added tuple extraction: `response = result[0] if isinstance(result, tuple) else result`

### 3. DeepTeam SDK Usage
**Problem:** Code was using `RedTeamer` directly instead of the recommended `red_team()` function.

**Solution:**
- Updated `services/red_team_service.py` to use the top-level `red_team()` function
- This matches the official DeepTeam SDK documentation and examples
- Ensures proper initialization and error handling

## Changes Made

### Files Modified

1. **`config/settings.py`**
   - Changed `max_concurrent` default from `10` to `3`
   - Added comment explaining rate limit constraint

2. **`apps/simple_model_app.py`**
   - Fixed tuple return handling in `model_callback()`

3. **`apps/rag_app.py`**
   - Fixed tuple return handling in `model_callback()`

4. **`apps/chatbot_app.py`**
   - Fixed tuple return handling in `model_callback()`

5. **`apps/agent_app.py`**
   - Fixed tuple return handling in `model_callback()`

6. **`services/red_team_service.py`**
   - Switched from `RedTeamer` direct usage to `red_team()` function
   - Removed unnecessary error handling for ZeroDivisionError
   - Added better logging for configuration

7. **`README.md`**
   - Updated `MAX_CONCURRENT` default to `3`
   - Added explanation about rate limits

## Testing Recommendations

1. **Test with reduced concurrency:**
   ```bash
   export MAX_CONCURRENT=3
   python main.py run --demo vulnerability
   ```

2. **If still hitting rate limits, reduce further:**
   ```bash
   export MAX_CONCURRENT=2
   python main.py run --demo vulnerability
   ```

3. **Monitor for rate limit errors:**
   - Check logs for "429 Too Many Requests" errors
   - If errors persist, consider adding delays between requests
   - Or reduce `attacks_per_vulnerability_type` to generate fewer test cases

## Anthropic Rate Limits

According to Anthropic's documentation:
- **Concurrent connections:** Limited (varies by tier)
- **Requests per minute:** Varies by model and tier
- **Best practice:** Use `max_concurrent=3` or lower for reliable operation

## Future Improvements

If rate limiting continues to be an issue, consider:
1. Adding exponential backoff retry logic (DeepEval already has this)
2. Implementing request queuing with delays
3. Reducing `attacks_per_vulnerability_type` to generate fewer test cases
4. Using a different model for simulator/evaluation that has higher rate limits

