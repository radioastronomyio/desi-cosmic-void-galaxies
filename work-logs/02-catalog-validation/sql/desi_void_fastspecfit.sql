CREATE SCHEMA "raw_catalogs";

CREATE TABLE "fastspecfit_galaxies" (
  "targetid" int8 PRIMARY KEY NOT NULL,
  "ra" float8,
  "dec" float8,
  "z" float8,
  "z_err" float4,
  "logmstar" float4,
  "logmstar_err" float4,
  "sfr" float4,
  "sfr_err" float4,
  "age_gyr" float4,
  "metallicity" float4,
  "d4000" float4,
  "healpix_source" int4,
  "source_file" varchar(255)
);

CREATE TABLE "raw_catalogs"."fastspecfit_galaxies" (
  "targetid" int8 PRIMARY KEY NOT NULL,
  "ra" float8 NOT NULL,
  "dec" float8 NOT NULL,
  "z" float8 NOT NULL,
  "z_err" float8,
  "logmstar" float4,
  "logmstar_err" float4,
  "sfr" float4,
  "sfr_err" float4,
  "age_gyr" float4,
  "metallicity" float4,
  "d4000" float4,
  "healpix_id" int4 NOT NULL,
  "source_file" varchar(255) NOT NULL,
  "ingestion_timestamp" timestamptz DEFAULT (now())
);

CREATE INDEX "idx_fastspecfit_dec" ON "fastspecfit_galaxies" USING BTREE ("dec");

CREATE INDEX "idx_fastspecfit_logmstar" ON "fastspecfit_galaxies" USING BTREE ("logmstar");

CREATE INDEX "idx_fastspecfit_ra" ON "fastspecfit_galaxies" USING BTREE ("ra");

CREATE INDEX "idx_fastspecfit_z" ON "fastspecfit_galaxies" USING BTREE ("z");

CREATE INDEX "idx_fastspecfit_galaxies_logmstar" ON "raw_catalogs"."fastspecfit_galaxies" USING BTREE ("logmstar");

CREATE INDEX "idx_fastspecfit_galaxies_sfr" ON "raw_catalogs"."fastspecfit_galaxies" USING BTREE ("sfr");

CREATE INDEX "idx_fastspecfit_galaxies_z" ON "raw_catalogs"."fastspecfit_galaxies" USING BTREE ("z");

COMMENT ON TABLE "raw_catalogs"."fastspecfit_galaxies" IS 'Galaxy properties from the DESI DR1 FastSpecFit catalog, containing over 6 million objects.';

COMMENT ON COLUMN "raw_catalogs"."fastspecfit_galaxies"."targetid" IS 'Unique DESI target identifier (64-bit integer).';

COMMENT ON COLUMN "raw_catalogs"."fastspecfit_galaxies"."logmstar" IS 'Log10 of the total stellar mass in solar mass units.';

COMMENT ON COLUMN "raw_catalogs"."fastspecfit_galaxies"."sfr" IS 'Star Formation Rate in solar mass per year units.';

COMMENT ON COLUMN "raw_catalogs"."fastspecfit_galaxies"."healpix_id" IS 'The HEALPix pixel number of the source file.';
