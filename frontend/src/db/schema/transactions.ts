import { pgTable, uuid, varchar, integer, decimal, timestamp, index } from 'drizzle-orm/pg-core'
import { brands } from './brands'
import { categories } from './categories'
import { geography } from './geography'
import { panelists } from './panelists'
import { generations } from './generations'
import { incomeBands } from './income-bands'

// FR-6.1: 10M+ synthetic transactions
// FR-6.2: TimescaleDB hypertable with daily chunk intervals
export const transactions = pgTable('transactions', {
  id: uuid('id').primaryKey().defaultRandom(),
  transactionTimestamp: timestamp('transaction_timestamp', { withTimezone: true }).notNull(),

  // Foreign keys
  panelistId: uuid('panelist_id').notNull().references(() => panelists.id),
  brandId: integer('brand_id').notNull().references(() => brands.id),
  categoryId: integer('category_id').notNull().references(() => categories.id),
  geographyId: integer('geography_id').notNull().references(() => geography.id),

  // Panelist demographics (denormalized for query performance)
  generationId: varchar('generation_id', { length: 20 }).notNull().references(() => generations.id),
  incomeBandId: varchar('income_band_id', { length: 20 }).notNull().references(() => incomeBands.id),

  // Transaction details
  transactionAmount: decimal('transaction_amount', { precision: 10, scale: 2 }).notNull(),
  cardType: varchar('card_type', { length: 20 }).notNull(), // credit, debit, prepaid, corporate
  paymentNetwork: varchar('payment_network', { length: 20 }).notNull(), // visa, mastercard, amex, discover
  channel: varchar('channel', { length: 20 }).notNull(), // online, in-store, mobile

  // Time dimensions (for efficient aggregation without timezone conversion)
  dayOfWeek: varchar('day_of_week', { length: 10 }).notNull(),
  hourOfDay: integer('hour_of_day').notNull(),

  // Tenant for future multi-tenancy support
  tenantId: uuid('tenant_id').defaultRandom(),

  // Audit timestamps
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
}, (table) => [
  // Composite indexes for efficient filtering on common query patterns
  // FR-6.8: Composite indexes on (timestamp, brand_id, category_id)
  index('idx_transactions_timestamp_brand').on(table.transactionTimestamp, table.brandId),
  index('idx_transactions_timestamp_category').on(table.transactionTimestamp, table.categoryId),
  index('idx_transactions_timestamp_geo').on(table.transactionTimestamp, table.geographyId),
  index('idx_transactions_timestamp_income').on(table.transactionTimestamp, table.incomeBandId),
  index('idx_transactions_timestamp_generation').on(table.transactionTimestamp, table.generationId),

  // Indexes for dimension lookups
  index('idx_transactions_panelist').on(table.panelistId),
  index('idx_transactions_brand').on(table.brandId),
  index('idx_transactions_category').on(table.categoryId),
  index('idx_transactions_geography').on(table.geographyId),
])

export type Transaction = typeof transactions.$inferSelect
export type NewTransaction = typeof transactions.$inferInsert
