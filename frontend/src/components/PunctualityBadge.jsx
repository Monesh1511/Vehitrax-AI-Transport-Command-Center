import React from 'react';

export function PunctualityBadge({ status }) {
  let badgeClass = 'badge ';
  if (status === 'On Time') badgeClass += 'success';
  else if (status === 'Delayed') badgeClass += 'danger';
  else badgeClass += 'warning';

  return (
    <span className={badgeClass}>
      {status}
    </span>
  );
}
