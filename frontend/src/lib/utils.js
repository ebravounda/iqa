import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

export function formatDateTime(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function formatTime(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function formatCurrency(amount, currency = 'EUR') {
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency
  }).format(amount);
}

export function getDaysRemaining(endDate) {
  if (!endDate) return 0;
  const end = new Date(endDate);
  const now = new Date();
  const diff = end - now;
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

export function getMembershipStatus(membership) {
  if (!membership) return { status: 'none', label: 'Sin membresía', color: 'danger' };
  
  const daysRemaining = getDaysRemaining(membership.end_date);
  
  if (daysRemaining < 0) {
    return { status: 'expired', label: 'Vencida', color: 'danger' };
  } else if (daysRemaining <= 5) {
    return { status: 'expiring', label: `Vence en ${daysRemaining} días`, color: 'warning' };
  } else {
    return { status: 'active', label: 'Activa', color: 'success' };
  }
}
