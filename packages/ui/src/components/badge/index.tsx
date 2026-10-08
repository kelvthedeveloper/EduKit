import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {}

export const Badge: React.FC<BadgeProps> = (props) => {
  return <span {...props} />;
};

export default Badge;
