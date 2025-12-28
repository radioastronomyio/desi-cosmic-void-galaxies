CREATE SCHEMA "raw_catalogs";

CREATE TABLE "desivast_revolver_voids" (
  "id" SERIAL PRIMARY KEY NOT NULL,
  "ra" float8,
  "dec" float8,
  "radius_mpc_h" float4,
  "effective_radius_mpc_h" float4,
  "effective_radius_uncert" float4,
  "original_void_index" int4,
  "edge_flag" int4,
  "x_mpc_h" float4,
  "y_mpc_h" float4,
  "z_mpc_h" float4,
  "redshift" float4,
  "source_file" varchar(255),
  "galactic_cap" varchar(3)
);

CREATE TABLE "desivast_vide_voids" (
  "id" SERIAL PRIMARY KEY NOT NULL,
  "ra" float8,
  "dec" float8,
  "radius_mpc_h" float4,
  "effective_radius_mpc_h" float4,
  "effective_radius_uncert" float4,
  "original_void_index" int4,
  "edge_flag" int4,
  "x_mpc_h" float4,
  "y_mpc_h" float4,
  "z_mpc_h" float4,
  "redshift" float4,
  "source_file" varchar(255),
  "galactic_cap" varchar(3)
);

CREATE TABLE "desivast_zobov_voids" (
  "id" SERIAL PRIMARY KEY NOT NULL,
  "ra" float8,
  "dec" float8,
  "radius_mpc_h" float4,
  "effective_radius_mpc_h" float4,
  "effective_radius_uncert" float4,
  "original_void_index" int4,
  "edge_flag" int4,
  "x_mpc_h" float4,
  "y_mpc_h" float4,
  "z_mpc_h" float4,
  "redshift" float4,
  "source_file" varchar(255),
  "galactic_cap" varchar(3)
);

CREATE TABLE "desivast_voidfinder_maximals" (
  "id" SERIAL PRIMARY KEY NOT NULL,
  "ra" float8,
  "dec" float8,
  "radius_mpc_h" float4,
  "effective_radius_mpc_h" float4,
  "effective_radius_uncert" float4,
  "original_void_index" int4,
  "edge_flag" int4,
  "x_mpc_h" float4,
  "y_mpc_h" float4,
  "z_mpc_h" float4,
  "redshift" float4,
  "source_file" varchar(255),
  "galactic_cap" varchar(3)
);

CREATE TABLE "raw_catalogs"."desivast_voids" (
  "void_id" SERIAL PRIMARY KEY NOT NULL,
  "algorithm" varchar(20) NOT NULL,
  "original_void_index" int8 NOT NULL,
  "ra" float8 NOT NULL,
  "dec" float8 NOT NULL,
  "x_mpc_h" float8,
  "y_mpc_h" float8,
  "z_mpc_h" float8,
  "radius_mpc_h" float8,
  "edge_flag" int4,
  "redshift" float8,
  "depth" int8,
  "tot_area" float8,
  "edge_area" float8,
  "gal" int8,
  "out_flag" int4,
  "void0" int8,
  "void1" int8,
  "x1" float8,
  "y1" float8,
  "z1" float8,
  "x2" float8,
  "y2" float8,
  "z2" float8,
  "x3" float8,
  "y3" float8,
  "z3" float8,
  "zone" int8,
  "target" int8,
  "g2v" int8,
  "g2v2" int8,
  "gid" int8,
  "n_x" float8,
  "n_y" float8,
  "n_z" float8,
  "p1_x" float8,
  "p1_y" float8,
  "p1_z" float8,
  "p2_x" float8,
  "p2_y" float8,
  "p2_z" float8,
  "p3_x" float8,
  "p3_y" float8,
  "p3_z" float8,
  "r_eff" float8,
  "r_eff_uncert" float8,
  "galactic_cap" varchar(3) NOT NULL,
  "source_file" varchar(255) NOT NULL,
  "ingestion_timestamp" timestamptz DEFAULT (now())
);

CREATE INDEX "idx_revolver_dec" ON "desivast_revolver_voids" USING BTREE ("dec");

CREATE INDEX "idx_revolver_ra" ON "desivast_revolver_voids" USING BTREE ("ra");

CREATE INDEX "idx_vide_dec" ON "desivast_vide_voids" USING BTREE ("dec");

CREATE INDEX "idx_vide_ra" ON "desivast_vide_voids" USING BTREE ("ra");

CREATE INDEX "idx_zobov_dec" ON "desivast_zobov_voids" USING BTREE ("dec");

CREATE INDEX "idx_zobov_ra" ON "desivast_zobov_voids" USING BTREE ("ra");

CREATE INDEX "idx_voidfinder_dec" ON "desivast_voidfinder_maximals" USING BTREE ("dec");

CREATE INDEX "idx_voidfinder_ra" ON "desivast_voidfinder_maximals" USING BTREE ("ra");

CREATE INDEX "unique_void_entry" ON "raw_catalogs"."desivast_voids" USING BTREE ("algorithm", "galactic_cap", "original_void_index");

CREATE INDEX "idx_desivast_voids_algorithm" ON "raw_catalogs"."desivast_voids" USING BTREE ("algorithm");

CREATE INDEX "idx_desivast_voids_radius" ON "raw_catalogs"."desivast_voids" USING BTREE ("radius_mpc_h");

COMMENT ON TABLE "raw_catalogs"."desivast_voids" IS 'Unified table containing cosmic void properties from all DESIVAST algorithms (REVOLVER, VIDE, ZOBOV, VoidFinder).';

COMMENT ON COLUMN "raw_catalogs"."desivast_voids"."void_id" IS 'Unique serial identifier for each void entry in the database.';

COMMENT ON COLUMN "raw_catalogs"."desivast_voids"."algorithm" IS 'The void-finding algorithm used to identify this void.';

COMMENT ON COLUMN "raw_catalogs"."desivast_voids"."original_void_index" IS 'The original VOID or MAXIMAL index from the source FITS file.';

COMMENT ON COLUMN "raw_catalogs"."desivast_voids"."ra" IS 'Right Ascension in degrees (J2000).';

COMMENT ON COLUMN "raw_catalogs"."desivast_voids"."dec" IS 'Declination in degrees (J2000).';

COMMENT ON COLUMN "raw_catalogs"."desivast_voids"."radius_mpc_h" IS 'Void radius in Mpc/h.';

COMMENT ON COLUMN "raw_catalogs"."desivast_voids"."r_eff" IS 'Effective radius, specific to the VoidFinder algorithm.';

COMMENT ON COLUMN "raw_catalogs"."desivast_voids"."galactic_cap" IS 'The galactic cap (NGC or SGC) of the observation.';

COMMENT ON COLUMN "raw_catalogs"."desivast_voids"."source_file" IS 'The name of the source FITS file from which this record was extracted.';
