import { pgTable, serial, varchar, timestamp, integer, index } from 'drizzle-orm/pg-core'

// FR-6.5: Brand tier classification (luxury, premium, mid-market, value)
// FR-6.5: Brand archetype (fast_casual, discount_retailer, department_store, subscription)
// FR-6.5: Brand-to-parent mapping for corporate hierarchies
export const brands = pgTable('brands', {
  id: serial('id').primaryKey(),
  name: varchar('name', { length: 100 }).notNull().unique(),
  tier: varchar('tier', { length: 20 }).notNull(),
  archetype: varchar('archetype', { length: 50 }).notNull(),
  parentCompanyId: integer('parent_company_id').references(() => brands.id, { onDelete: 'set null' }),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
}, (table) => [
  index('idx_brands_tier').on(table.tier),
  index('idx_brands_archetype').on(table.archetype),
  index('idx_brands_parent').on(table.parentCompanyId),
])

export type Brand = typeof brands.$inferSelect
export type NewBrand = typeof brands.$inferInsert
