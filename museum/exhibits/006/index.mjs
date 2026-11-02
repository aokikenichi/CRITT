import {makeAdapter} from '../shared/adapter.mjs';
import {createNative} from './native.mjs?v=20261103';
export default meta=>makeAdapter(meta,createNative);
