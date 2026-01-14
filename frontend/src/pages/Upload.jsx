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
  { value: 'auto', label: '自动' },
  { value: 'generic', label: '通用' },
  { value: 'mc_notional', label: 'MarketChameleon 名义值' },
  { value: 'mc_volume', label: 'MarketChameleon 成交量' },
  { value: 'mc_volatility', label: 'MarketChameleon 波动率' }
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
        message.warning('解析失败，请查看警告。');
      }
    } catch (error) {
      message.error('图片解析失败。');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!parseResult?.columns?.length) {
      message.warning('没有可保存的解析数据。');
      return;
    }
    if (!datasetName) {
      message.warning('请输入数据集名称。');
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
      message.success('数据集已保存。');
      navigate(`/analysis?dataset_id=${response.data.dataset_id}`);
    } catch (error) {
      message.error('保存数据集失败。');
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
          <Card title="上传表格图片">
            <div className="table-toolbar">
              <Select
                value={parser}
                onChange={setParser}
                options={parserOptions}
                style={{ width: 260 }}
              />
              <Input
                placeholder="数据集名称"
                value={datasetName}
                onChange={(event) => setDatasetName(event.target.value)}
                style={{ width: 240 }}
              />
              <Button type="primary" onClick={handleSave} disabled={loading}>
                保存数据集
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
              <p className="ant-upload-text">点击或拖拽图片上传</p>
              <p className="ant-upload-hint">支持表格截图（png/jpg）。</p>
            </Dragger>
          </Card>
        </Col>
        <Col span={24}>
          {imageUrl && (
            <Card title="预览">
              <Image src={imageUrl} alt="预览" style={{ maxHeight: 320 }} />
            </Card>
          )}
        </Col>
        <Col span={24}>
          {parseResult?.warnings?.length > 0 && (
            <Alert
              type={parseResult.ok ? 'warning' : 'error'}
              message="警告"
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
          <Card title="解析表格" loading={loading}>
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
