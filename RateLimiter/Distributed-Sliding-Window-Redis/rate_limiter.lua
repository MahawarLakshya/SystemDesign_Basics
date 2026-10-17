-- Redis 7+: Sliding-window log rate limiter (atomic check-and-insert)
-- KEYS[1]: per-user Sorted Set key
-- ARGV[1]: maximum allowed requests
-- ARGV[2]: window duration in milliseconds
-- ARGV[3]: unique request ID

local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local request_id = ARGV[3]

-- Validate arguments before making any changes
if not limit or limit < 1 or limit % 1 ~= 0 then
    return redis.error_reply('limit must be a positive integer')
end
if not window or window < 1 or window % 1 ~= 0 then
    return redis.error_reply('window must be a positive integer in milliseconds')
end
if not request_id or request_id == '' then
    return redis.error_reply('request_id must not be empty')
end

-- Use the same Redis clock across all application servers
local clock = redis.call('TIME')
local now = tonumber(clock[1]) * 1000 + math.floor(tonumber(clock[2]) / 1000)
local cutoff = now - window

-- Remove timestamps outside the rolling window
redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)

-- Check the active request count
local count = redis.call('ZCARD', key)
if count >= limit then
    return {0, count}
end

-- Accept and record the request as one atomic state transition
redis.call('ZADD', key, now, request_id)
redis.call('PEXPIRE', key, window)
return {1, count + 1}
