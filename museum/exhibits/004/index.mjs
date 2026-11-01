import {makeAdapter} from '../shared/adapter.mjs';
import {createNative} from './native.mjs';
export default meta=>makeAdapter(meta,createNative);
