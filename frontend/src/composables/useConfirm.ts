import { inject } from 'vue'
import type { InjectionKey, Ref } from 'vue'

export interface ConfirmOptions {
  title?: string
  message: string
  variant?: 'default' | 'danger'
  confirmText?: string
  cancelText?: string
  /** Optional third button text. When clicked, confirm() resolves with 'alt' instead of true. */
  altText?: string
  /** Variant for the alt button (default: 'default'). */
  altVariant?: 'default' | 'primary' | 'danger' | 'success'
  /** When set, show a "Don't ask again" checkbox. Value is the localStorage key. */
  dontAskKey?: string
  /** When set, show an additional checkbox with this label above the footer buttons.
   *  If `checkboxRef` is provided, its value is two-way bound (caller reads it after confirm). */
  checkboxLabel?: string
  /** Default value of the custom checkbox (used when checkboxRef is not provided). */
  checkboxDefault?: boolean
  /** Optional external ref to two-way bind the custom checkbox state. */
  checkboxRef?: Ref<boolean>
}

export type ConfirmResult = boolean | 'alt'
export type ConfirmFn = (options: ConfirmOptions) => Promise<ConfirmResult>

export const confirmKey: InjectionKey<ConfirmFn> = Symbol('confirm')

export function useConfirm() {
  const confirm = inject(confirmKey)
  if (!confirm) throw new Error('useConfirm() requires <ConfirmProvider> in ancestor')
  return { confirm }
}
