import React from 'react';

export interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {}

export const Table: React.FC<TableProps> = (props) => {
  return <table {...props} />;
};

export default Table;
