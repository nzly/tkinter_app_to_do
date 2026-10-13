-- licenses table
create table public.licenses (
  key text not null,
  email text not null,
  status text null default 'active'::text,
  max_activations integer null default 2,
  activations jsonb null default '[]'::jsonb,
  created_at timestamp with time zone not null default timezone ('Pacific/Auckland'::text, now()),
  expiry_date_time timestamp with time zone null default timezone ('Pacific/Auckland'::text, now()),
  constraint licenses_pkey primary key (key)
) TABLESPACE pg_default;

-- users table
-- Create a users table with an auto-incrementing primary key
CREATE TABLE IF NOT EXISTS public.users (
    id BIGSERIAL PRIMARY KEY,        -- Automatically increments (1, 2, 3...)
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('Pacific/Auckland'::text, now()) NOT NULL,
    expiry_date_time timestamp with time zone null default timezone ('Pacific/Auckland'::text, now()),
    status TEXT default 'active' -- 'active', 'disabled', or 'expired'
);

-- INSERT public.users
INSERT INTO public.users (username, email, status)
VALUES 
    ('yun', 'yun@digitmind.com', 'active'),
    ('admin', 'admin@digitmind.com', 'active'),
    ('test', 'test@digitmind.com', 'disabled');

-- Enable Row Level Security (RLS) for protection
alter table public.licenses ENABLE row LEVEL SECURITY;
alter table public.users ENABLE row LEVEL SECURITY;

-- Deny direct public access (client apps interact safely via Service Role key / Server API)
create policy "No direct public access" on public.licenses for all using (false);

select  * from public.licenses;
select * from public.users;

-- Update licenses
select now();

SELECT * FROM public.licenses WHERE key = 'PRO-KEY-1234-5678';
SELECT '2026-10-13 02:17:58.347845+00'::timestamp <= now()::timestamp;

UPDATE public.licenses -- Replace 'licenses' with your actual table name if different
SET status = LOWER('Disabled')
WHERE status = LOWER('Active')
  AND expiry_date_time IS NOT NULL
  AND expiry_date_time <= NOW();

-- UPDATE licenses status
update public.licenses
set status = 'active'
where key = 'PRO-KEY-1234-5678';

-- Update timestamp to NZ time zone
-- Update default value for created_at
ALTER TABLE public.licenses 
ALTER COLUMN created_at SET DEFAULT timezone('Pacific/Auckland'::text, now());

-- Update default value for expiry_date_time (if it uses a default)
ALTER TABLE public.licenses 
ALTER COLUMN expiry_date_time SET DEFAULT timezone('Pacific/Auckland'::text, now());

-- 1. Insert a test row without specifying dates
INSERT INTO public.licenses (key, email, status, max_activations, activations) VALUES ('PRO-KEY-1234-1111', 'developer@digitmind.co.nz', 'active', 2, '["WINDOWS-X86_64-9876543210","Windows-AMD64-163164138462239"]');

-- 2. View the row with the timestamp explicitly displayed in NZ time
SELECT key, status, 
       created_at AT TIME ZONE 'Pacific/Auckland' AS created_nz,
       expiry_date_time AT TIME ZONE 'Pacific/Auckland' AS expiry_nz
FROM public.licenses
ORDER BY key DESC;
