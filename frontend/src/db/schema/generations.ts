import { pgTable, varchar, integer, timestamp } from 'drizzle-orm/pg-core'

// FR-6.7: Generational preferences for demographic correlations
export const generations = pgTable('generations', {
  id: varchar('id', { length: 20 }).primaryKey(),
  name: varchar('name', { length: 50 }).notNull(),
  birthYearStart: integer('birth_year_start').notNull(),
  birthYearEnd: integer('birth_year_end').notNull(),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
})

export type Generation = typeof generations.$inferSelect
export type NewGeneration = typeof generations.$inferInsert
