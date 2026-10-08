import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Card: React.FC<CardProps> = (props) => {
  return <div {...props} />;
};

export default Card;
