create table if not exists public.licenses (
  key TEXT primary key,
  email TEXT not null,
  status TEXT default 'active', -- 'active', 'revoked', or 'expired'
  max_activations INT default 2,
  activations JSONB default '[]'::jsonb, -- Array of Hardware IDs
  created_at timestamp with time zone default timezone ('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS) for protection
alter table public.licenses ENABLE row LEVEL SECURITY;

-- Deny direct public access (client apps interact safely via Service Role key / Server API)
create policy "No direct public access" on public.licenses for all using (false);

select  * from public.licenses;

-------------------------------------------------------------
-- Cereate pg_cron to run the  below function daily
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Daily batch run to update lience key status
-- Create a function that performs the expiration check and update
CREATE OR REPLACE FUNCTION public.check_and_disable_expired_licenses()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE public.licenses -- Replace 'licenses' with your actual table name if different
  SET status = 'Disabled'
  WHERE status = 'Active'
    AND expiry_date_time IS NOT NULL
    AND expiry_date_time <= NOW();
END;
$$;

-- Schedule the function to run daily
SELECT cron.schedule(
  'disable-expired-licenses-daily', -- Job name
  '0 0 * * *',                      -- Cron schedule (Every day at 00:00 UTC)
  $$SELECT public.check_and_disable_expired_licenses();$$
);

-- Check if the scheduled job is existing
SELECT * FROM cron.job;

-- Check Job Execution History & Logs
SELECT j.jobname, d.status, d.return_message, d.start_time, d.end_time 
FROM cron.job_run_details d
JOIN cron.job j ON d.jobid = j.jobid
ORDER BY d.start_time DESC 
LIMIT 10;

-- Modify or Re-create the Job via SQL
-- 1. Remove the old job if it exists
SELECT cron.unschedule('disable-expired-licenses-daily');

-- 2. Re-create it fresh
SELECT cron.schedule(
  'disable-expired-licenses-daily',
  '0 0 * * *',
  $$SELECT public.check_and_disable_expired_licenses();$$
);
-------------------------------------------------------------
[
  {
    "schedule": 1
  }
]
-------------------------------------------------------------
