import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Button,
  Card,
  Col,
  Image,
  Input,
  Layout,
  message,
  Row,
  Select,
  Upload
} from 'antd';
import client from '../api/client';
import EditableTable from '../components/EditableTable';

const { Dragger } = Upload;

const parserOptions = [
  { value: 'auto', label: 'Auto' },
  { value: 'generic', label: 'Generic' },
  { value: 'mc_notional', label: 'MarketChameleon Notional' },
  { value: 'mc_volume', label: 'MarketChameleon Volume' },
  { value: 'mc_volatility', label: 'MarketChameleon Volatility' }
];

const UploadPage = () => {
  const navigate = useNavigate();
  const [imageUrl, setImageUrl] = useState('');
  const [parser, setParser] = useState('auto');
  const [parseResult, setParseResult] = useState(null);
  const [tableRows, setTableRows] = useState([]);
  const [datasetName, setDatasetName] = useState('');
  const [loading, setLoading] = useState(false);

  const handleParse = async (file) => {
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await client.post(`/uploads/table-image?parser=${parser}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setParseResult(response.data);
      const rowsWithKey = (response.data.rows || []).map((row, idx) => ({
        key: String(idx),
        ...row
      }));
      setTableRows(rowsWithKey);
      if (!response.data.ok) {
        message.warning('Parsing failed, see warnings.');
      }
    } catch (error) {
      message.error('Failed to parse image.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!parseResult?.columns?.length) {
      message.warning('No parsed data to save.');
      return;
    }
    if (!datasetName) {
      message.warning('Please enter dataset name.');
      return;
    }
    const rows = tableRows.map((row) => {
      const cleaned = { ...row };
      delete cleaned.key;
      return cleaned;
    });
    try {
      const response = await client.post('/datasets', {
        name: datasetName,
        columns: parseResult.columns,
        rows,
        source_parse_id: parseResult.parse_id
      });
      message.success('Dataset saved.');
      navigate(`/analysis?dataset_id=${response.data.dataset_id}`);
    } catch (error) {
      message.error('Failed to save dataset.');
    }
  };

  const columns = (parseResult?.columns || []).map((col) => ({
    title: col,
    dataIndex: col,
    width: 140
  }));

  return (
    <Layout>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="Upload Table Image">
            <div className="table-toolbar">
              <Select
                value={parser}
                onChange={setParser}
                options={parserOptions}
                style={{ width: 260 }}
              />
              <Input
                placeholder="Dataset Name"
                value={datasetName}
                onChange={(event) => setDatasetName(event.target.value)}
                style={{ width: 240 }}
              />
              <Button type="primary" onClick={handleSave} disabled={loading}>
                Save Dataset
              </Button>
            </div>
            <Dragger
              accept=".png,.jpg,.jpeg"
              showUploadList={false}
              customRequest={({ file }) => {
                const url = URL.createObjectURL(file);
                setImageUrl(url);
                handleParse(file);
              }}
            >
              <p className="ant-upload-drag-icon">📄</p>
              <p className="ant-upload-text">Click or drag an image to upload</p>
              <p className="ant-upload-hint">Supports table screenshots (png/jpg).</p>
            </Dragger>
          </Card>
        </Col>
        <Col span={24}>
          {imageUrl && (
            <Card title="Preview">
              <Image src={imageUrl} alt="Preview" style={{ maxHeight: 320 }} />
            </Card>
          )}
        </Col>
        <Col span={24}>
          {parseResult?.warnings?.length > 0 && (
            <Alert
              type={parseResult.ok ? 'warning' : 'error'}
              message="Warnings"
              description={
                <ul>
                  {parseResult.warnings.map((warn, idx) => (
                    <li key={idx}>{warn}</li>
                  ))}
                </ul>
              }
            />
          )}
        </Col>
        <Col span={24}>
          <Card title="Parsed Table" loading={loading}>
            <EditableTable
              columns={columns}
              dataSource={tableRows}
              confMatrix={parseResult?.cell_conf}
              onChange={setTableRows}
            />
          </Card>
        </Col>
      </Row>
    </Layout>
  );
};

export default UploadPage;
