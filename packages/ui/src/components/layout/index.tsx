import React from 'react';

export interface LayoutProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Layout: React.FC<LayoutProps> = (props) => {
  return <div {...props} />;
};

export default Layout;
