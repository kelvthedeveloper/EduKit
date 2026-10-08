import { z } from 'zod';

export const commonSchema = z.object({});

export type CommonSchema = z.infer<typeof commonSchema>;
