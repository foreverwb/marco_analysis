import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Button, Card, Col, Layout, Row, Select, Table, Alert } from 'antd';
import client from '../api/client';

const AnalysisPage = () => {
  const [searchParams] = useSearchParams();
  const [datasets, setDatasets] = useState([]);
  const [datasetId, setDatasetId] = useState(searchParams.get('dataset_id') || '');
  const [heatmap, setHeatmap] = useState({ rows: [], warnings: [] });
  const [momentum, setMomentum] = useState({ rows: [], warnings: [] });

  const fetchDatasets = async () => {
    const response = await client.get('/datasets');
    setDatasets(response.data || []);
  };

  const fetchAnalysis = async (id) => {
    if (!id) {
      return;
    }
    const [heatmapRes, momentumRes] = await Promise.all([
      client.get(`/analysis/heatmap?dataset_id=${id}`),
      client.get(`/analysis/momentum-stocks?dataset_id=${id}&top=10`)
    ]);
    setHeatmap(heatmapRes.data);
    setMomentum(momentumRes.data);
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  useEffect(() => {
    if (datasetId) {
      fetchAnalysis(datasetId);
    }
  }, [datasetId]);

  const heatmapColumns = heatmap.rows.length
    ? Object.keys(heatmap.rows[0]).map((key) => ({ title: key, dataIndex: key }))
    : [];
  const momentumColumns = momentum.rows.length
    ? Object.keys(momentum.rows[0]).map((key) => ({ title: key, dataIndex: key }))
    : [];

  return (
    <Layout>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="Select Dataset">
            <Row gutter={12} align="middle">
              <Col>
                <Select
                  style={{ width: 280 }}
                  value={datasetId}
                  onChange={setDatasetId}
                  placeholder="Choose dataset"
                  options={datasets.map((item) => ({
                    value: item.id,
                    label: `${item.name} (${item.row_count} rows)`
                  }))}
                />
              </Col>
              <Col>
                <Button onClick={fetchDatasets}>Refresh</Button>
              </Col>
            </Row>
          </Card>
        </Col>
        <Col span={24}>
          {heatmap.warnings?.length > 0 && (
            <Alert
              type="warning"
              message="Heatmap warnings"
              description={
                <ul>
                  {heatmap.warnings.map((warn, idx) => (
                    <li key={idx}>{warn}</li>
                  ))}
                </ul>
              }
            />
          )}
        </Col>
        <Col span={24}>
          <Card title="Heat Map Table">
            <Table
              rowKey={(record) => record.symbol || record.Symbol || JSON.stringify(record)}
              columns={heatmapColumns}
              dataSource={heatmap.rows}
              pagination={{ pageSize: 8 }}
              scroll={{ x: true }}
            />
          </Card>
        </Col>
        <Col span={24}>
          {momentum.warnings?.length > 0 && (
            <Alert
              type="warning"
              message="Momentum warnings"
              description={
                <ul>
                  {momentum.warnings.map((warn, idx) => (
                    <li key={idx}>{warn}</li>
                  ))}
                </ul>
              }
            />
          )}
        </Col>
        <Col span={24}>
          <Card title="Momentum Stocks">
            <Table
              rowKey={(record) => record.symbol || record.Symbol || JSON.stringify(record)}
              columns={momentumColumns}
              dataSource={momentum.rows}
              pagination={{ pageSize: 8 }}
              scroll={{ x: true }}
            />
          </Card>
        </Col>
      </Row>
    </Layout>
  );
};

export default AnalysisPage;
