<!-- src/views/ApiListPage/ApiListPage.vue -->
<template>
  <div class="dashboard-container">
    <el-button type="primary" :icon="Plus" @click="openAddDialog" class="add-button">
      新增API卡片
    </el-button>

    <el-row :gutter="20">
      <el-col
          v-for="card in apiCards"
          :key="card.id"
          :xs="24"
          :sm="24"
          :md="12"
          :lg="12"
          :xl="12"
          class="card-col"
      >
        <ApiCardComponent
            :card="card"
            :state="cardStates[card.id]"
            @edit="openEditDialog"
            @delete="deleteCard"
            @fetch="fetchCardApi"
        />
      </el-col>
    </el-row>

    <!-- 新增/编辑卡片弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEditMode ? '编辑API卡片' : '新增API卡片'" width="600px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="卡片名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="接口URL" prop="url">
          <el-input v-model="form.url" placeholder="例如: /api/users" />
        </el-form-item>
        <el-form-item label="请求方法" prop="method">
          <el-select v-model="form.method" style="width: 100%;">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="form.method === 'GET'" label="URL参数">
          <div v-for="(param, index) in form.params" :key="index" class="param-item">
            <el-switch v-model="param.enabled" class="param-switch" />
            <el-input v-model="param.key" placeholder="Key" class="param-input" />
            <span>:</span>
            <el-input v-model="param.value" placeholder="Value" class="param-input" />
            <el-button type="danger" :icon="Delete" circle plain @click="removeParam(index)" />
          </div>
          <el-button type="primary" plain @click="addParam">添加参数</el-button>
        </el-form-item>

        <el-form-item v-if="form.method === 'POST' || form.method === 'PUT'" label="请求体 (Body)">
          <el-input
              v-model="form.body"
              type="textarea"
              :rows="6"
              placeholder='请输入JSON格式的数据, e.g.,&#10;{&#10;  "title": "foo",&#10;  "body": "bar"&#10;}'
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleConfirm">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { ApiCard } from '@/types/api'
import { useApiCards } from '@/hooks/useApiCards'
import ApiCardComponent from './components/ApiCardComponent.vue'

const { apiCards, cardStates, addCard, updateCard, deleteCard, fetchCardApi } = useApiCards()

const dialogVisible = ref(false)
const isEditMode = ref(false)
const formRef = ref<FormInstance>()
const initialFormState = (): Omit<ApiCard, 'id'> => ({ name: '', url: '', method: 'GET', params: [{ key: '', value: '', enabled: true }], body: '' })
let form = reactive(initialFormState())

const rules: FormRules = {
  name: [{ required: true, message: '请输入卡片名称', trigger: 'blur' }],
  url: [{ required: true, message: '请输入接口URL', trigger: 'blur' }],
}

const addParam = () => { if (!form.params) form.params = []; form.params.push({ key: '', value: '', enabled: true }) }
const removeParam = (index: number) => form.params?.splice(index, 1)

const resetForm = () => { Object.assign(form, initialFormState()); isEditMode.value = false; nextTick(() => formRef.value?.clearValidate()) }

const openAddDialog = () => { resetForm(); dialogVisible.value = true }

const openEditDialog = (card: ApiCard) => {
  resetForm()
  isEditMode.value = true
  Object.assign(form, JSON.parse(JSON.stringify(card)))
  if (!form.params) form.params = [{ key: '', value: '', enabled: true }]
  dialogVisible.value = true
}

const handleConfirm = async () => {
  if (!formRef.value) return
  await formRef.value.validate((valid) => {
    if (valid) {
      const cardData = JSON.parse(JSON.stringify(form))
      if (isEditMode.value && cardData.id) {
        updateCard(cardData)
      } else {
        addCard(cardData)
      }
      dialogVisible.value = false
    }
  })
}
</script>

<style scoped>
.dashboard-container {
  max-width: 100%;
  height: 100%;
  margin: 0;
  padding: 30px;
  overflow-y: auto;
  background-color: var(--bg-color-deep-space);
  box-sizing: border-box;
}

.add-button {
  margin-bottom: 25px;
  background: rgba(100, 255, 218, 0.1);
  border: 1px solid var(--primary-accent-color);
  color: var(--primary-accent-color);
  transition: all 0.2s;
}
.add-button:hover {
  background: var(--primary-accent-color);
  color: #0a192f;
}

.card-col { margin-bottom: 20px; }

/* Dialog Styles Tweaks (if needed specific to this page) */
.param-item { display: flex; align-items: center; margin-bottom: 15px; }
.param-switch { margin-right: 15px; flex-shrink: 0; }
.param-input { margin: 0 5px; flex: 1; }
</style>