import { pgTable, serial, char, varchar, timestamp, index } from 'drizzle-orm/pg-core'

// FR-6.3: State (51 values)
// FR-6.3: CBSA/Metro Area (350-400 values)
// FR-6.3: Urban/Suburban/Rural classification
export const geography = pgTable('geography', {
  id: serial('id').primaryKey(),
  stateCode: char('state_code', { length: 2 }).notNull(),
  stateName: varchar('state_name', { length: 100 }).notNull(),
  cbsaCode: varchar('cbsa_code', { length: 10 }),
  cbsaName: varchar('cbsa_name', { length: 200 }),
  urbanClass: varchar('urban_class', { length: 20 }).notNull(), // urban, suburban, rural
  zip3: char('zip3', { length: 3 }),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
}, (table) => [
  index('idx_geography_state').on(table.stateCode),
  index('idx_geography_cbsa').on(table.cbsaCode),
  index('idx_geography_urban_class').on(table.urbanClass),
  index('idx_geography_zip3').on(table.zip3),
])

export type Geography = typeof geography.$inferSelect
export type NewGeography = typeof geography.$inferInsert
