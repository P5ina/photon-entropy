package entropy

import (
	"crypto/sha256"
	"encoding/binary"
	"sync"
)

type Pool struct {
	mu       sync.RWMutex
	data     []byte
	maxSize  int
	position int
}

func NewPool(maxSize int) *Pool {
	return &Pool{
		data:    make([]byte, 0, maxSize),
		maxSize: maxSize,
	}
}

func (p *Pool) Add(samples []int) {
	p.mu.Lock()
	defer p.mu.Unlock()

	for _, sample := range samples {
		lsb := byte(sample & 0xFF)
		if len(p.data) < p.maxSize {
			p.data = append(p.data, lsb)
		} else {
			p.data[p.position] = lsb
			p.position = (p.position + 1) % p.maxSize
		}
	}
}

func (p *Pool) Size() int {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return len(p.data)
}

func (p *Pool) GetBytes(n int) []byte {
	p.mu.Lock()
	defer p.mu.Unlock()

	if len(p.data) == 0 {
		return nil
	}

	result := make([]byte, 0, n)
	for len(result) < n {
		hash := sha256.Sum256(p.data)
		p.mixPool(hash[:])
		result = append(result, hash[:min(n-len(result), 32)]...)
	}

	return result[:n]
}

func (p *Pool) GetInt(min, max int64) (int64, bool) {
	if min >= max {
		return 0, false
	}

	bytes := p.GetBytes(8)
	if bytes == nil {
		return 0, false
	}

	raw := binary.BigEndian.Uint64(bytes)
	rangeSize := uint64(max - min)
	value := min + int64(raw%rangeSize)

	return value, true
}

func (p *Pool) mixPool(hash []byte) {
	for i := 0; i < len(p.data) && i < len(hash); i++ {
		p.data[i] ^= hash[i]
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
