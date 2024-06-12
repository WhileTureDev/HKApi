'use client';

import { useRouter } from 'next/navigation';
import { useEffect, ComponentType } from 'react';

const withAuth = <P extends object>(WrappedComponent: ComponentType<P>): ComponentType<P> => {
  return (props: P) => {
    const router = useRouter();

    useEffect(() => {
      const token = localStorage.getItem('token');
      if (!token) {
        router.push('/');
      }
    }, [router]);

    return <WrappedComponent {...props} />;
  };
};

export default withAuth;
