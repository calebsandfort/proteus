import { pgTable, serial, varchar, timestamp, index } from 'drizzle-orm/pg-core'

// FR-6.4: Level 1 - Style Classification (Discretionary, Consumer Staples, Services, Transportation)
// FR-6.4: Level 2 - Spending Category (35-45 categories)
// FR-6.4: Level 3 - Merchant Group (200-400 subcategories)
export const categories = pgTable('categories', {
  id: serial('id').primaryKey(),
  level1: varchar('level1', { length: 50 }).notNull(), // Discretionary, Consumer Staples, Services, Transportation
  level2: varchar('level2', { length: 100 }).notNull(), // Grocery, Restaurant, Apparel, Travel, etc.
  level3: varchar('level3', { length: 100 }).notNull(), // Subcategory
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
}, (table) => [
  index('idx_categories_level1').on(table.level1),
  index('idx_categories_level2').on(table.level2),
  index('idx_categories_level3').on(table.level3),
])

export type Category = typeof categories.$inferSelect
export type NewCategory = typeof categories.$inferInsert
