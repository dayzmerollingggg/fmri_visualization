export const metadata = {
  title: 'fMRI Visualization',
  description: 'fMRI data viewer and analysis interface',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: 'system-ui, sans-serif' }}>
        {children}
      </body>
    </html>
  );
}
