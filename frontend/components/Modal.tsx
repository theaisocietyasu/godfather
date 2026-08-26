'use client';

import { ReactNode } from 'react';
import { Dialog, DialogPanel, DialogTitle } from '@headlessui/react';
import { X as XIcon } from 'lucide-react';
import clsx from 'clsx';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  /** Max width class for the panel. Defaults to a mid-size dialog. */
  maxWidthClassName?: string;
}

export default function Modal({ open, onClose, title, children, footer, maxWidthClassName = 'max-w-2xl' }: ModalProps) {
  return (
    <Dialog open={open} onClose={onClose} transition className="relative z-50">
      <div
        className="fixed inset-0 bg-bg/70 backdrop-blur-sm transition duration-150 data-closed:opacity-0"
        aria-hidden="true"
      />

      <div className="fixed inset-0 flex w-screen items-center justify-center p-4">
        <DialogPanel
          transition
          className={clsx(
            'glass-strong flex max-h-[85vh] w-full flex-col overflow-hidden rounded-xl',
            'transition duration-150 ease-out data-closed:scale-95 data-closed:opacity-0',
            maxWidthClassName
          )}
        >
          <div className="flex items-center justify-between border-b border-border px-6 py-4">
            <DialogTitle className="text-base font-semibold text-text">{title}</DialogTitle>
            <button
              onClick={onClose}
              className="rounded-md p-1.5 text-text-secondary hover:bg-surface-hover hover:text-text"
              aria-label="Close"
            >
              <XIcon className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6">{children}</div>

          {footer && <div className="flex justify-end gap-3 border-t border-border px-6 py-4">{footer}</div>}
        </DialogPanel>
      </div>
    </Dialog>
  );
}
