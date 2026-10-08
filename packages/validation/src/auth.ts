import { z } from 'zod';

export const loginSchema = z.object({
  identifier: z
    .string()
    .min(1, 'Identifier (email, phone, or username) is required')
    .trim(),
  password: z
    .string()
    .min(1, 'Password is required'),
  remember: z.boolean().optional().default(false),
  device_id: z.string().optional(),
  device_name: z.string().optional(),
});

export type LoginInput = z.infer<typeof loginSchema>;

export const passwordChangeSchema = z
  .object({
    old_password: z.string().min(1, 'Current password is required'),
    new_password: z
      .string()
      .min(8, 'New password must be at least 8 characters long')
      .regex(/[A-Z]/, 'New password must contain at least one uppercase letter')
      .regex(/[0-9]/, 'New password must contain at least one number'),
    confirm_password: z.string().min(1, 'Password confirmation is required'),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'New passwords do not match',
    path: ['confirm_password'],
  });

export type PasswordChangeInput = z.infer<typeof passwordChangeSchema>;

export const passwordResetRequestSchema = z.object({
  identifier: z
    .string()
    .min(1, 'Email, phone, or username is required')
    .trim(),
});

export type PasswordResetRequestInput = z.infer<typeof passwordResetRequestSchema>;

export const passwordResetConfirmSchema = z
  .object({
    token: z.string().min(1, 'Reset token is required'),
    new_password: z
      .string()
      .min(8, 'New password must be at least 8 characters long')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[0-9]/, 'Password must contain at least one number'),
    confirm_password: z.string().min(1, 'Please confirm your new password'),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });

export type PasswordResetConfirmInput = z.infer<typeof passwordResetConfirmSchema>;

export const emailVerifySchema = z.object({
  token: z.string().min(1, 'Verification token is required'),
});

export type EmailVerifyInput = z.infer<typeof emailVerifySchema>;

export const phoneVerifySchema = z.object({
  phone: z.string().min(5, 'Valid phone number is required'),
  code: z
    .string()
    .min(4, 'Verification code must be at least 4 digits')
    .max(8, 'Verification code cannot exceed 8 digits')
    .regex(/^\d+$/, 'Code must be numeric'),
});

export type PhoneVerifyInput = z.infer<typeof phoneVerifySchema>;
