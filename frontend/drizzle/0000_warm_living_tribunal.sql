CREATE TABLE "account" (
	"id" text PRIMARY KEY NOT NULL,
	"account_id" text NOT NULL,
	"provider_id" text NOT NULL,
	"user_id" text NOT NULL,
	"access_token" text,
	"refresh_token" text,
	"id_token" text,
	"access_token_expires_at" timestamp,
	"refresh_token_expires_at" timestamp,
	"scope" text,
	"password" text,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "session" (
	"id" text PRIMARY KEY NOT NULL,
	"expires_at" timestamp NOT NULL,
	"token" text NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	"ip_address" text,
	"user_agent" text,
	"user_id" text NOT NULL,
	CONSTRAINT "session_token_unique" UNIQUE("token")
);
--> statement-breakpoint
CREATE TABLE "user" (
	"id" text PRIMARY KEY NOT NULL,
	"name" text NOT NULL,
	"email" text NOT NULL,
	"email_verified" boolean DEFAULT false NOT NULL,
	"image" text,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "user_email_unique" UNIQUE("email")
);
--> statement-breakpoint
CREATE TABLE "verification" (
	"id" text PRIMARY KEY NOT NULL,
	"identifier" text NOT NULL,
	"value" text NOT NULL,
	"expires_at" timestamp NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "brands" (
	"id" serial PRIMARY KEY NOT NULL,
	"name" varchar(100) NOT NULL,
	"tier" varchar(20) NOT NULL,
	"archetype" varchar(50) NOT NULL,
	"parent_company_id" integer,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "brands_name_unique" UNIQUE("name")
);
--> statement-breakpoint
CREATE TABLE "categories" (
	"id" serial PRIMARY KEY NOT NULL,
	"level1" varchar(50) NOT NULL,
	"level2" varchar(100) NOT NULL,
	"level3" varchar(100) NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "geography" (
	"id" serial PRIMARY KEY NOT NULL,
	"state_code" char(2) NOT NULL,
	"state_name" varchar(100) NOT NULL,
	"cbsa_code" varchar(10),
	"cbsa_name" varchar(200),
	"urban_class" varchar(20) NOT NULL,
	"zip3" char(3),
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "generations" (
	"id" varchar(20) PRIMARY KEY NOT NULL,
	"name" varchar(50) NOT NULL,
	"birth_year_start" integer NOT NULL,
	"birth_year_end" integer NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "income_bands" (
	"id" varchar(20) PRIMARY KEY NOT NULL,
	"name" varchar(50) NOT NULL,
	"min_income" integer NOT NULL,
	"max_income" integer,
	"income_multiplier" numeric(4, 2) DEFAULT '1.0' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "panelists" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"income_band_id" varchar(20) NOT NULL,
	"generation_id" varchar(20) NOT NULL,
	"geography_id" integer NOT NULL,
	"panel_start_date" date NOT NULL,
	"panel_weight" numeric(10, 4) NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "transactions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"transaction_timestamp" timestamp with time zone NOT NULL,
	"panelist_id" uuid NOT NULL,
	"brand_id" integer NOT NULL,
	"category_id" integer NOT NULL,
	"geography_id" integer NOT NULL,
	"generation_id" varchar(20) NOT NULL,
	"income_band_id" varchar(20) NOT NULL,
	"transaction_amount" numeric(10, 2) NOT NULL,
	"card_type" varchar(20) NOT NULL,
	"payment_network" varchar(20) NOT NULL,
	"channel" varchar(20) NOT NULL,
	"day_of_week" varchar(10) NOT NULL,
	"hour_of_day" integer NOT NULL,
	"tenant_id" uuid DEFAULT gen_random_uuid(),
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "account" ADD CONSTRAINT "account_user_id_user_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "session" ADD CONSTRAINT "session_user_id_user_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "brands" ADD CONSTRAINT "brands_parent_company_id_brands_id_fk" FOREIGN KEY ("parent_company_id") REFERENCES "public"."brands"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "panelists" ADD CONSTRAINT "panelists_income_band_id_income_bands_id_fk" FOREIGN KEY ("income_band_id") REFERENCES "public"."income_bands"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "panelists" ADD CONSTRAINT "panelists_generation_id_generations_id_fk" FOREIGN KEY ("generation_id") REFERENCES "public"."generations"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "panelists" ADD CONSTRAINT "panelists_geography_id_geography_id_fk" FOREIGN KEY ("geography_id") REFERENCES "public"."geography"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_panelist_id_panelists_id_fk" FOREIGN KEY ("panelist_id") REFERENCES "public"."panelists"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_brand_id_brands_id_fk" FOREIGN KEY ("brand_id") REFERENCES "public"."brands"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_category_id_categories_id_fk" FOREIGN KEY ("category_id") REFERENCES "public"."categories"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_geography_id_geography_id_fk" FOREIGN KEY ("geography_id") REFERENCES "public"."geography"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_generation_id_generations_id_fk" FOREIGN KEY ("generation_id") REFERENCES "public"."generations"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_income_band_id_income_bands_id_fk" FOREIGN KEY ("income_band_id") REFERENCES "public"."income_bands"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "idx_brands_tier" ON "brands" USING btree ("tier");--> statement-breakpoint
CREATE INDEX "idx_brands_archetype" ON "brands" USING btree ("archetype");--> statement-breakpoint
CREATE INDEX "idx_brands_parent" ON "brands" USING btree ("parent_company_id");--> statement-breakpoint
CREATE INDEX "idx_categories_level1" ON "categories" USING btree ("level1");--> statement-breakpoint
CREATE INDEX "idx_categories_level2" ON "categories" USING btree ("level2");--> statement-breakpoint
CREATE INDEX "idx_categories_level3" ON "categories" USING btree ("level3");--> statement-breakpoint
CREATE INDEX "idx_geography_state" ON "geography" USING btree ("state_code");--> statement-breakpoint
CREATE INDEX "idx_geography_cbsa" ON "geography" USING btree ("cbsa_code");--> statement-breakpoint
CREATE INDEX "idx_geography_urban_class" ON "geography" USING btree ("urban_class");--> statement-breakpoint
CREATE INDEX "idx_geography_zip3" ON "geography" USING btree ("zip3");--> statement-breakpoint
CREATE INDEX "idx_panelists_weight" ON "panelists" USING btree ("panel_weight");--> statement-breakpoint
CREATE INDEX "idx_panelists_income_band" ON "panelists" USING btree ("income_band_id");--> statement-breakpoint
CREATE INDEX "idx_panelists_generation" ON "panelists" USING btree ("generation_id");--> statement-breakpoint
CREATE INDEX "idx_panelists_geography" ON "panelists" USING btree ("geography_id");--> statement-breakpoint
CREATE INDEX "idx_panelists_start_date" ON "panelists" USING btree ("panel_start_date");--> statement-breakpoint
CREATE INDEX "idx_transactions_timestamp_brand" ON "transactions" USING btree ("transaction_timestamp","brand_id");--> statement-breakpoint
CREATE INDEX "idx_transactions_timestamp_category" ON "transactions" USING btree ("transaction_timestamp","category_id");--> statement-breakpoint
CREATE INDEX "idx_transactions_timestamp_geo" ON "transactions" USING btree ("transaction_timestamp","geography_id");--> statement-breakpoint
CREATE INDEX "idx_transactions_timestamp_income" ON "transactions" USING btree ("transaction_timestamp","income_band_id");--> statement-breakpoint
CREATE INDEX "idx_transactions_timestamp_generation" ON "transactions" USING btree ("transaction_timestamp","generation_id");--> statement-breakpoint
CREATE INDEX "idx_transactions_panelist" ON "transactions" USING btree ("panelist_id");--> statement-breakpoint
CREATE INDEX "idx_transactions_brand" ON "transactions" USING btree ("brand_id");--> statement-breakpoint
CREATE INDEX "idx_transactions_category" ON "transactions" USING btree ("category_id");--> statement-breakpoint
CREATE INDEX "idx_transactions_geography" ON "transactions" USING btree ("geography_id");