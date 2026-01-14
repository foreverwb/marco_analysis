import React from 'react';
import { Route, Routes, Navigate, Link } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import UploadPage from './pages/Upload.jsx';
import AnalysisPage from './pages/Analysis.jsx';

const { Header, Content } = Layout;

const App = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529' }}>
        <Menu
          theme="dark"
          mode="horizontal"
          defaultSelectedKeys={['upload']}
          items={[
            { key: 'upload', label: <Link to="/upload">Upload</Link> },
            { key: 'analysis', label: <Link to="/analysis">Analysis</Link> }
          ]}
        />
      </Header>
      <Content style={{ padding: '24px' }}>
        <Routes>
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
        </Routes>
      </Content>
    </Layout>
  );
};

export default App;
