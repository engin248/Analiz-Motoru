import '@testing-library/jest-dom'

// Mock ESM-only modules
jest.mock('react-markdown', () => (props: any) => {
    return <>{ props.children } </>
})

jest.mock('remark-gfm', () => () => { })
jest.mock('rehype-raw', () => () => { })
