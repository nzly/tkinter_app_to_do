CREATE TABLE public.licenses (
    key TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    status TEXT DEFAULT 'active', -- 'active', 'revoked', or 'expired'
    max_activations INT DEFAULT 2,
    activations JSONB DEFAULT '[]'::jsonb, -- Array of Hardware IDs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security (RLS) for protection
ALTER TABLE public.licenses ENABLE ROW LEVEL SECURITY;

-- Deny direct public access (client apps interact safely via Service Role key / Server API)
CREATE POLICY "No direct public access" ON public.licenses 
FOR ALL USING (false);

-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.licenses (
  key text NOT NULL,
  email text NOT NULL,
  status text DEFAULT 'active'::text,
  max_activations integer DEFAULT 2,
  activations jsonb DEFAULT '[]'::jsonb,
  created_at timestamp with time zone NOT NULL DEFAULT timezone('utc'::text, now()),
  CONSTRAINT licenses_pkey PRIMARY KEY (key)
);
