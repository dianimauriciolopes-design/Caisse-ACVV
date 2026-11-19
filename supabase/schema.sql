-- Schéma Supabase pour Caisse-ACVV
-- À exécuter une fois dans l'éditeur SQL du projet Supabase (SQL Editor → New query)

create table if not exists stands (
  id bigint generated always as identity primary key,
  nom text not null,
  description text,
  actif boolean not null default true
);

create table if not exists articles (
  id bigint generated always as identity primary key,
  stand_id bigint references stands(id) on delete cascade,
  nom text not null,
  prix numeric(10,2) not null,
  emoji text default '🍺',
  actif boolean not null default true
);

create table if not exists transactions (
  id bigint generated always as identity primary key,
  stand_id bigint references stands(id),
  stand_nom text,
  montant numeric(10,2) not null,
  mode_paiement text not null check (mode_paiement in ('cash', 'twint')),
  statut text not null default 'ok' check (statut in ('ok', 'annule')),
  detail_articles jsonb not null default '[]',
  created_at timestamptz not null default now()
);

-- ───────── RLS ─────────
-- L'app appelle Supabase directement depuis le navigateur avec la clé "anon".
-- Ces règles ouvrent lecture/écriture publiques (protégées côté UI par un mot
-- de passe pour /admin et /dashboard, pas par une vraie authentification).

alter table stands enable row level security;
alter table articles enable row level security;
alter table transactions enable row level security;

create policy "stands select" on stands for select using (true);
create policy "stands insert" on stands for insert with check (true);
create policy "stands update" on stands for update using (true) with check (true);

create policy "articles select" on articles for select using (true);
create policy "articles insert" on articles for insert with check (true);
create policy "articles update" on articles for update using (true) with check (true);

create policy "transactions select" on transactions for select using (true);
create policy "transactions insert" on transactions for insert with check (true);
create policy "transactions update" on transactions for update using (true) with check (true);

-- ───────── DONNÉES PAR DÉFAUT ─────────

do $$
declare
  id_caisse bigint;
  id_bar bigint;
  id_cocktails bigint;
begin
  if not exists (select 1 from stands) then
    insert into stands (nom, description) values ('Caisse principale', 'Entrées') returning id into id_caisse;
    insert into stands (nom, description) values ('Bar principal', 'Boissons & plats') returning id into id_bar;
    insert into stands (nom, description) values ('Bar à cocktails', 'avec ou sans alcool, consigne 2chf') returning id into id_cocktails;

    insert into articles (stand_id, nom, prix, emoji) values
      (id_caisse, 'Entrée enfant', 10.00, '🎟️'),
      (id_caisse, 'Entrée adulte', 20.00, '🎟️'),

      (id_bar, 'Grillades', 12.00, '🥩'),
      (id_bar, 'Bifanas', 8.00, '🫓'),
      (id_bar, 'Frites', 5.00, '🍟'),
      (id_bar, 'Minérale 3DL (Coca,..)', 3.00, '🥤'),
      (id_bar, 'Eau Minéral 1.5LT', 6.00, '💧'),
      (id_bar, 'Bière', 4.00, '🍺'),
      (id_bar, 'Bière sans alcool', 4.00, '🍺'),
      (id_bar, 'Mateus Rosé', 15.00, '🍷'),
      (id_bar, 'Vin au verre', 4.00, '🍷'),
      (id_bar, 'Grogu', 5.00, '🥃'),
      (id_bar, 'Red bull', 5.00, '🥤'),
      (id_bar, 'Café', 3.00, '☕'),

      (id_cocktails, 'Virgin Mojito (+ 2chf)', 10.00, '🍸'),
      (id_cocktails, 'Mojito (+ 2chf)', 12.00, '🍸'),
      (id_cocktails, 'Caipirinha (+ 2chf)', 10.00, '🍹'),
      (id_cocktails, 'Spritz (+ 2chf)', 10.00, '🍹');
  end if;
end $$;
